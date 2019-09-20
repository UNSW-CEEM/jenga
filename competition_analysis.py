from application.model.bidstack import BidStack
from application.model.dispatch import DispatchLoad
from application.model.participants import ParticipantService
from application.util.interpolation_timeseries import InterpolationTimeseries
from application.machine_learning.random_forests import run_random_forest_price

from application.graph.network_rsi import LMPFactory
from competition_modelling import tables, plotting



import os
import csv
import pendulum
import numpy as np

from competition_modelling import config

from application.util.pickling import getFromPickle, saveToPickle

participant_service = ParticipantService()

from application.model.demand import Demand
from application.model.price import Price
# from similarity.normalized_levenshtein import NormalizedLevenshtein

# normalized_levenshtein = NormalizedLevenshtein()

from similarity.qgram import QGram

qgram = QGram(2)

RESEARCH_HOURS = [0,6,12,18,24]
# RESEARCH_HOURS = [12]



PICKLE_FILENAME = 'competition_analysis.pkl'

def process(start_date, end_date):
    """
        the 'main' function here
        loops through all the required time periods, generates results. 
    """
    # Grabbing old results from saved file. If you change the metrics, delete this file first so that the metrics are updated. Otherwise new calcs will be skipped on any time period previously examined. 
    saved_timeseries = getFromPickle(PICKLE_FILENAME)
    timeseries = saved_timeseries if saved_timeseries else {}

    current = start_date
    while current < end_date:
        if current.hour in RESEARCH_HOURS and current.minute == 0 and current not in timeseries:
            timeseries[current] = {}
            timeseries = process_bidstacks(current, timeseries)
            timeseries = process_dispatch(current, timeseries)
            print(current)
            # print(timeseries[current])
        current = current.add(minutes=30)

    saveToPickle(timeseries, PICKLE_FILENAME)
    return timeseries

def process_dispatch(dt, timeseries={}):

    # print("Dispatch Analysis", dt)
    query = DispatchLoad.objects(SETTLEMENTDATE=dt).fields(DUID=1, TOTALCLEARED=1)
    dispatches = [d for d in query]
    # print(dispatches)
    # Get the dispatch of each firm in the market. 
    firm_dispatch = {}
    total_dispatch = 0
    for state in config.STATES:
        for dispatch in dispatches:
            participant_state = participant_service.get_state(dispatch.DUID)
            if participant_state == state or state == 'ALL':
                if "RT_" not in dispatch.DUID:
                    firm = participant_service.get_parent_firm(dispatch.DUID)
                    firm_dispatch[firm] = dispatch.TOTALCLEARED if not firm in firm_dispatch else firm_dispatch[firm] + dispatch.TOTALCLEARED
                    total_dispatch += dispatch.TOTALCLEARED
                
        # Get the market share of each firm in the market, based on dispatch
        firm_dispatch_shares = {firm: float(firm_dispatch[firm]) / float(total_dispatch) for firm in firm_dispatch}
        
        # Calculate and record market competition indicators.
        
        timeseries[dt]['hhi_dispatch_'+state] = get_hhi(firm_dispatch_shares)
        timeseries[dt]['entropy_dispatch_'+state] = get_entropy(firm_dispatch_shares)
        timeseries[dt]['four_firm_concentration_ratio_dispatch_'+state] = get_four_firm_concentration_ratio(firm_dispatch_shares)
        
        # print(dt)
        
    return timeseries
    

def process_bidstacks(dt, timeseries={}):
    """ Derives competition indicators from bids submitted by generators.  """
    # Get bidstacks for every time period. 
    bidstack = BidStack.objects.get(trading_period=dt)
    # Filter based on hour so we don't process tonnes of them
    timeseries[dt] = {} if not dt in timeseries else timeseries[dt]
    # Grab demand data. 
    demand_req = Demand.objects(date_time=dt)
    regional_demand = {d.region:d.demand for d in demand_req}
    total_demand = int(float(sum([regional_demand[region] for region in regional_demand])))
    # Grab price data
    price_req = Price.objects(date_time = dt, price_type='AEMO_SPOT')
    regional_prices = {p.region: p.price for p in price_req}
    # Get a dict of all the residual supply indices, augmented with max network flows. 
    network_residual_supply_indices = get_network_extended_residual_supply_indices(bidstack, regional_demand)
    network_extended_capacity_hhi = get_network_extended_capacity_hhi(bidstack, regional_demand)
    # Record price and demand. 
    timeseries[dt]['weighted_average_price'] = float(sum([regional_prices[p] * regional_demand[p] for p in regional_prices])) / float(total_demand)
    timeseries[dt]['demand_ALL'] = total_demand
    timeseries[dt]['price'] =  regional_prices
    for key in regional_demand:
        timeseries[dt]['demand_'+key] = regional_demand[key]
    for key in regional_prices:
        timeseries[dt]['price_'+key] = regional_prices[key]
            

    for state in config.STATES:
        # Get a dict of all the bid-based market shares for this time period
        generator_bid_shares = get_generator_bid_market_shares(bidstack, state)
        # Get a dict of all the residual supply indices for this time period
        residual_supply_indices = get_residual_supply_indices(bidstack, total_demand, state)
        # Get a dict of all the pivotal supplier indices for this time period.
        pivotal_supplier_indices = get_pivotal_supplier_indices(bidstack, total_demand, state)
        # Loop through every state and analyse / record
        if state != "ALL":
            # Get a dict of all firm weighted offers
            firm_weighted_offer_prices = get_firm_volume_weighted_offer_price(bidstack, state)
            for firm in firm_weighted_offer_prices:
                timeseries[dt][firm.lower()+'_weighted_offer_price_'+state] = firm_weighted_offer_prices[firm]
            # Calculate average NERSI for all firms in the state.
            for firm in network_residual_supply_indices[state]:
                timeseries[dt][firm.lower()+'_nersi_'+state] = network_residual_supply_indices[state][firm]
            timeseries[dt]['average_nersi_'+state] = float(sum([network_residual_supply_indices[state][firm] for firm in network_residual_supply_indices[state]])) / float(len(network_residual_supply_indices[state]))
            timeseries[dt]['minimum_nersi_'+state] = min([network_residual_supply_indices[state][firm] for firm in network_residual_supply_indices[state]])
            # Record network-extended HHI
            timeseries[dt]['nechhi_'+state] = network_extended_capacity_hhi[state]

        # Record results.
        timeseries[dt]['hhi_bids_'+state] =  get_hhi(generator_bid_shares)
        timeseries[dt]['entropy_bids_'+state] =  get_entropy(generator_bid_shares)
        timeseries[dt]['four_firm_concentration_ratio_bids_'+state] = get_four_firm_concentration_ratio(generator_bid_shares)
        timeseries[dt]['average_rsi_'+state] = float(sum([residual_supply_indices[firm] for firm in residual_supply_indices])) / float(len([f for f in residual_supply_indices]))
        timeseries[dt]['minimum_rsi_'+state] = min([residual_supply_indices[firm] for firm in residual_supply_indices])
        timeseries[dt]['sum_psi_'+state] = sum([pivotal_supplier_indices[firm] for firm in pivotal_supplier_indices])
        
        # Record RSI and PSI for each firm. 
        for firm in residual_supply_indices:
            timeseries[dt][firm.lower()+'_rsi_'+state] = residual_supply_indices[firm]
        for firm in pivotal_supplier_indices:
            timeseries[dt][firm.lower()+'_psi_'+state] = pivotal_supplier_indices[firm]
            
    return timeseries


def get_firm_volume_weighted_offer_price(bidstack, state):
    participants = bidstack.getParticipants()
    offers = {}
    weighted_prices = {}
    for participant in participants:
        participant_state = participant_service.get_state(participant)
        if participant_state == state:
            if "RT_" not in participant:
                bid = bidstack.getBid(participant) 
                firm = participant_service.get_parent_firm(participant)
                for band in range(1,9):
                    volume = bid.get_volume(band)
                    price = bid.get_price(band)
                    offers[firm] = [] if not firm in offers else offers[firm]
                    offers[firm].append({'price':price, 'volume':volume})
    
    for firm in offers:
        total_volume = float(sum([offer['volume'] for offer in offers[firm]]))
        if total_volume > 0:
            weighted_price = 0
            for offer in offers[firm]:
                weight = float(offer['volume']) / total_volume
                weighted_price += weight * float(offer['price'])
        else:
            weighted_price = None
        weighted_prices[firm] = weighted_price
    
    return weighted_prices


def get_generator_bid_market_shares(bidstack, state='ALL'):
    """Gets the market share of each participant. At the moment this is on a generator basis. Need to make a version that gets it on a firm basis - thats the real bullseye here. """
    participants = bidstack.getParticipants()
    shares = {}
    total_volume = 0

    for participant in participants:
        participant_state = participant_service.get_state(participant)
        # If the participant is in the desired state, or if we want all config.states...
        if participant_state == state or state == 'ALL':
            if "RT_" not in participant:
                bid = bidstack.getBid(participant) 
                firm = participant_service.get_parent_firm(participant)
                for band in range(1,9):
                    volume = bid.get_volume(band)
                    total_volume += volume
                    shares[firm] = volume if not firm in shares else shares[firm] + volume
    # Divide all by total volume to get the share rather than gross volume. 
    for firm in shares:
        shares[firm] = float(shares[firm]) / float(total_volume)
    return shares

def get_pivotal_supplier_indices(bidstack, demand, state='ALL'):
    """
        Pivotal supplier index for a generator is 1 if demand can be satisfied without it, otherwise 0. 
    """
    participants = bidstack.getParticipants()
    volumes = {}
    psi = {}
    total_volume = 0

    for participant in participants:
        participant_state = participant_service.get_state(participant)
        # If the participant is in the desired state, or if we want all config.states...
        if participant_state == state or state == 'ALL':
            if "RT_" not in participant:
                bid = bidstack.getBid(participant)
                firm = participant_service.get_parent_firm(participant)
                for band in range(1,9):
                    volume = bid.get_volume(band)
                    total_volume += volume
                    volumes[firm] = volume if not firm in volumes else volumes[firm] + volume
    # Divide all by total volume to get the share rather than gross volume. 
    for firm in volumes:
        if total_volume - volumes[firm] >= demand:
            psi[firm] = 0
        else:
            psi[firm] = 1
    return psi
    

def get_residual_supply_indices(bidstack, demand, state='ALL'):
    """
    The Residual Supply Index (RSI) is the ratio of the total capacity of all the other generators in the market to the total market demand at a point in time. 
    """
    participants = bidstack.getParticipants()
    volumes = {}
    rsi = {}
    total_volume = 0

    for participant in participants:
        participant_state = participant_service.get_state(participant)
        # If the participant is in the desired state, or if we want all config.states...
        if participant_state == state or state == 'ALL':
            if "RT_" not in participant:
                bid = bidstack.getBid(participant) 
                firm = participant_service.get_parent_firm(participant)
                for band in range(1,9):
                    volume = bid.get_volume(band)
                    total_volume += volume
                    volumes[firm] = volume if not firm in volumes else volumes[firm] + volume
    # Divide all by total volume to get the share rather than gross volume. 
    for firm in volumes:
        rsi[firm] = float(total_volume - volumes[firm]) / float(demand)
    return rsi



def get_network_extended_residual_supply_indices(bidstack, regional_demand):
    """
        The Network-Extended Residual Supply Index (RSI) is the ratio of the total capacity of all the other generators in the market to the total market demand at a point in time. 
        It uses spare capacity in adjacent trading nodes (not from the firm under inspection), available via interconnectors, to increase the sum of available capacity.
        It hus produces a more relistic RSI that takes into account capacity available in other trading nodes.
    """
    participants = bidstack.getParticipants()
    volumes = {state:{} for state in config.STATES if state != 'ALL'}
    rsi = {state:{} for state in config.STATES if state != 'ALL'}
    total_volume = {state:0 for state in config.STATES if state != 'ALL'} 
    network_flow = LMPFactory().get_australian_nem()

    for participant in participants:
        # If the participant is a firm (not transmission or distributed generation)
        if "RT_" not in participant and "DG_" not in participant:
            state = participant_service.get_state(participant)
            volume = bidstack.getBid(participant).get_total_volume()
            firm = participant_service.get_parent_firm(participant)
            if state: #some participants dont have metadata.
                volumes[state][firm] = volume if not firm in volumes[state] else volumes[state][firm] + volume
                total_volume[state] += volume
            
    # Divide all by total volume to get the share rather than gross volume. 
    for state in volumes:
        for firm in volumes[state]:
            # Determine spare capacities of all other config.states. 
            spare_capacity = {}
            for other_state in regional_demand:
                if other_state != state:
                    firm_capacity = volumes[other_state][firm] if firm in volumes[other_state] else 0
                    spare_capacity[other_state] = max(total_volume[other_state] - regional_demand[other_state] - firm_capacity, 0)
            # Pass to the nersi flow calculator to find additional interstate capacity available.
            extra_interstate_capacity = network_flow.calculate_flow(state, spare_capacity)
            # Calculate and record the rsi
            rsi[state][firm] = float(total_volume[state] + extra_interstate_capacity - volumes[state][firm]) / float(regional_demand[state])
    return rsi

def get_network_extended_capacity_hhi(bidstack, regional_demand):
    """
        The Network-Extended Capacity Herfindahl Firschman (NE-C-HHI) is HHI extended to use the excess capacity of other config.states as an additional competitior in a given trading node. 
        'Capacity' means it is based on bids (rather than dispatch)
        It produces a more relistic HHI that takes into account capacity available in other trading nodes.
    """
    participants = bidstack.getParticipants()
    volumes = {state:{} for state in config.STATES if state != 'ALL'}
    hhi = {}
    total_volume = {state:0 for state in config.STATES if state != 'ALL'} 
    network_flow = LMPFactory().get_australian_nem()

    for participant in participants:
        # If the participant is a firm (not transmission or distributed generation)
        if "RT_" not in participant and "DG_" not in participant:
            state = participant_service.get_state(participant)
            volume = bidstack.getBid(participant).get_total_volume()
            firm = participant_service.get_parent_firm(participant)
            if state: #some participants dont have metadata.
                volumes[state][firm] = volume if not firm in volumes[state] else volumes[state][firm] + volume
                total_volume[state] += volume
            
    # Divide all by total volume to get the share rather than gross volume. 
    for state in volumes:
        # Determine spare capacities of all other config.states. 
        spare_capacity = {}
        for other_state in regional_demand:
            if other_state != state:
                spare_capacity[other_state] = max(total_volume[other_state] - regional_demand[other_state], 0)
        # Pass to the nersi flow calculator to find additional interstate capacity available.
        extra_interstate_capacity = network_flow.calculate_flow(state, spare_capacity)
        # Calculate and record the rsi
        volumes[state]['interconnectors'] = extra_interstate_capacity
        total_available_volume = sum([volumes[state][firm] for firm in volumes[state]])
        shares = {firm:volumes[state][firm]/total_available_volume for firm in volumes[state]}
        hhi[state] = get_hhi(shares)
    return hhi
    
def get_hhi(shares):
    """
        HHI is the sum of the squares of all the market shares (as a percentage not a decimal) of firms in a market. The higher the HHI, the more highly concentrated the market.
        Takes a shares dict - each participant name as key, their market share as value. 
        Returns HHI.
        """
    hhi = sum([shares[p] * 100 * shares[p] * 100 for p in shares])
    return hhi

def get_entropy(shares):
    """
        Entropy is sum of Si * log2 (1/Si) where Si is the share of the market of participant i, expressed as a fraction. 
        """
    entropy = sum([shares[p] * np.log2(1.0/ shares[p] ) for p in shares if shares[p] > 0])
    return entropy

def get_four_firm_concentration_ratio(shares):
    """
        Four firm concentration ratio is the sum of the four biggest market shares
        Takes a shares dict - each participant name as key, their market share as value. 
        Returns Four Firm Concentration Ratio.    
    """
    share_list = [shares[p] for p in shares]
    share_list = sorted(share_list, reverse=True)
    top_four = share_list[:4]
    return sum(top_four)


def settle(bidstack):
    participants = bidstack.getParticipants()
    simple_bids = []
    lrmc_bids = []
    srmc_bids = []
    # Grab the simple bids of each participant
    for participant in participants:
        if "RT_" not in participant: #there are a lot of 'RT_' bids that I suspect are Regional Transmission? They mess up everything. High volumes (like the entire NEM * 2-3)
            srmc = participant_service.get_srmc(participant)
            lrmc = participant_service.get_lrmc(participant)
            bid = bidstack.getBid(participant) 
            
            for band in range(1,9):
                price = bid.get_price(band)
                volume = bid.get_volume(band)
                if volume > 0:
                    simple_bids.append({'participant':participant, 'volume': volume, 'price':price,})
                    srmc_bids.append({'participant':participant, 'volume': volume, 'price':srmc})
                    lrmc_bids.append({'participant':participant, 'volume': volume, 'price':lrmc})
                    # if srmc == 0 or lrmc == 0:
                    #     fuelsource = participant_service.participant_metadata[participant]['fuel_source_descriptor'] if participant in participant_service.participant_metadata else "Not Found"
                    #     gentype = participant_service.participant_metadata[participant]['technology_type_descriptor'] if participant in participant_service.participant_metadata else "Not Found"
                    #     print("$0 bid by ", fuelsource, gentype, participant, volume)

    # Sort each bidstack by price
    simple_bids = sorted(simple_bids, key = lambda i: i['price'])
    srmc_bids = sorted(srmc_bids, key = lambda i: i['price'])
    lrmc_bids = sorted(lrmc_bids, key = lambda i: i['price'])

    return simple_bids, srmc_bids, lrmc_bids



def get_strike_price(bids, demand):
    cumulative_demand = 0
    for bid in bids:
        cumulative_demand += bid['volume']
        if cumulative_demand > demand:
        
            return bid['price']
    return 14000





if __name__=="__main__":
    start_date = pendulum.datetime(2018,1,1,12)
    end_date = pendulum.datetime(2018,12,27,12)
    timeseries = process(start_date, end_date)
    print([key for key in timeseries])
    plotting.plot_data(timeseries)
    tables.table_data(timeseries)