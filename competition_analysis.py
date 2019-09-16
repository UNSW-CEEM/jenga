from application.model.bidstack import BidStack
from application.model.dispatch import DispatchLoad
from application.model.participants import ParticipantService
from application.util.interpolation_timeseries import InterpolationTimeseries
from application.machine_learning.random_forests import run_random_forest_price

from application.graph.network_rsi import LMPFactory

from scipy.stats.stats import pearsonr

from prettytable import PrettyTable

import os
import csv
import pendulum
import numpy as np
import re

from application.util.pickling import getFromPickle, saveToPickle


from bokeh.layouts import column, gridplot
from bokeh.plotting import figure, show, output_file
from bokeh.models import LinearAxis, Range1d

from palettable.matplotlib import Plasma_20 as palette

participant_service = ParticipantService()

from application.model.demand import Demand
from application.model.price import Price
# from similarity.normalized_levenshtein import NormalizedLevenshtein

# normalized_levenshtein = NormalizedLevenshtein()

from similarity.qgram import QGram

qgram = QGram(2)

RESEARCH_HOURS = [0,6,12,18,24]

STATES = ['QLD', 'NSW', 'VIC', 'SA', 'TAS', 'ALL']

PICKLE_FILENAME = 'competition_analysis.pkl'

def process(start_date, end_date):
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
            print(timeseries[current])
        current = current.add(minutes=30)

    saveToPickle(timeseries, PICKLE_FILENAME)
    return timeseries

def process_dispatch(dt, timeseries={}):

    print("Dispatch Analysis", dt)
    query = DispatchLoad.objects(SETTLEMENTDATE=dt).fields(DUID=1, TOTALCLEARED=1)
    dispatches = [d for d in query]
    # print(dispatches)
    # Get the dispatch of each firm in the market. 
    firm_dispatch = {}
    total_dispatch = 0
    for state in STATES:
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

    print("Processing Bidstack")
    # Get bidstacks for every time period. 
    bidstack = BidStack.objects.get(trading_period=dt)
    print('Retrieved Bidstacks', bidstack)
    
    # Get the trading period label. 
    
    
    # Filter based on hour so we don't process tonnes of them
    timeseries[dt] = {} if not dt in timeseries else timeseries[dt]
    print("Bid Analysis", dt)
    # Grab the bids and order in economic dispatch order. 
    
    # simple_bids, srmc_bids, lrmc_bids = settle(bidstack)
    # dt = pendulum.instance(bidstack.trading_period)
    # Grab demand data. 
    demand_req = Demand.objects(date_time=dt)
    regional_demand = {d.region:d.demand for d in demand_req}
    total_demand = int(float(sum([regional_demand[region] for region in regional_demand])))
    
    # Grab price data
    price_req = Price.objects(date_time = dt, price_type='AEMO_SPOT')
    regional_prices = {p.region: p.price for p in price_req}
    # print(regional_prices)
    weighted_average_price = float(sum([regional_prices[p] * regional_demand[p] for p in regional_prices])) / float(total_demand)
    # print(weighted_average_price)

    # Get a dict of all the residual supply indices, augmented with max network flows. 
    network_residual_supply_indices = get_network_extended_residual_supply_indices(bidstack, regional_demand)
    
    timeseries[dt]['weighted_average_price'] = weighted_average_price
    
    timeseries[dt]['demand_ALL'] = total_demand
    timeseries[dt]['datetime'] =  dt
    timeseries[dt]['price'] =  regional_prices

    for key in regional_demand:
        timeseries[dt]['demand_'+key] = regional_demand[key]
    for key in regional_prices:
        timeseries[dt]['price_'+key] = regional_prices[key]
            

    for state in STATES:
        # Get a dict of all the bid-based market shares for this time period
        generator_bid_shares = get_generator_bid_market_shares(bidstack, state)

        # Get a dict of all the residual supply indices for this time period
        residual_supply_indices = get_residual_supply_indices(bidstack, total_demand, state)

        # Get a dict of all the pivotal supplier indices for this time period.
        pivotal_supplier_indices = get_pivotal_supplier_indices(bidstack, total_demand, state)

        
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

        # Record results.
        timeseries[dt]['hhi_bids_'+state] =  get_hhi(generator_bid_shares)
        timeseries[dt]['entropy_bids_'+state] =  get_entropy(generator_bid_shares)
        timeseries[dt]['four_firm_concentration_ratio_bids_'+state] = get_four_firm_concentration_ratio(generator_bid_shares)
        timeseries[dt]['average_rsi_'+state] = float(sum([residual_supply_indices[firm] for firm in residual_supply_indices])) / float(len([f for f in residual_supply_indices]))
        timeseries[dt]['minimum_rsi_'+state] = min([residual_supply_indices[firm] for firm in residual_supply_indices])
        timeseries[dt]['sum_psi_'+state] = sum([pivotal_supplier_indices[firm] for firm in pivotal_supplier_indices])
        
        for firm in residual_supply_indices:
            timeseries[dt][firm.lower()+'_rsi_'+state] = residual_supply_indices[firm]
        for firm in pivotal_supplier_indices:
            timeseries[dt][firm.lower()+'_psi_'+state] = pivotal_supplier_indices[firm]
            
    # print(timeseries[dt])

    print("Finished Processing Bidstack")
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
        # If the participant is in the desired state, or if we want all states...
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
        # If the participant is in the desired state, or if we want all states...
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
        # If the participant is in the desired state, or if we want all states...
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
    volumes = {state:{} for state in STATES if state != 'ALL'}
    rsi = {state:{} for state in STATES if state != 'ALL'}
    total_volume = {state:0 for state in STATES if state != 'ALL'} 
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
            # Determine spare capacities of all other states. 
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

def get_hhi_stat_table(timeseries):
    """Extracts a number of metrics related to HHI"""

    table = PrettyTable()
    table.field_names = ["Metric","Label", "Value"]

    MODERATELY_CONCENTRATED = 1500
    HIGHLY_CONCENTRATED = 2500
    total_count = {}
    moderately = {}
    highly = {}
    for t in timeseries:
        for key in timeseries[t]:
            if 'hhi_' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                moderately[key] = 0 if key not in moderately else moderately[key]
                highly[key] = 0 if key not in highly else highly[key]
                if timeseries[t][key] > HIGHLY_CONCENTRATED:
                    highly[key] += 1
                elif timeseries[t][key] > MODERATELY_CONCENTRATED:
                    moderately[key] += 1
    
    for key in total_count:
        table.add_row([key, "% Highly", 100.0 * float(highly[key])/ float(total_count[key])])
        table.add_row([key, "% Moderately", 100.0 * float(moderately[key])/ float(total_count[key])])
        # table.add_row([key, "Count Moderately", moderately[key]])
        # table.add_row([key, "Count Highly", highly[key]])
        # table.add_row([key, "Count Total", total_count[key] ])
    return table


def get_entropy_stat_table(timeseries):
    """Extracts a number of metrics related to entropy"""

    table = PrettyTable()
    table.field_names = ["Metric","Label", "Value"]

    THRESHOLD = 3.32
    HIGHLY_CONCENTRATED = 2500
    total_count = {}
    concentrated = {}
    
    for t in timeseries:
        for key in timeseries[t]:
            if 'entropy_' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                concentrated[key] = 0 if key not in concentrated else concentrated[key]
                if timeseries[t][key] < THRESHOLD:
                    concentrated[key] += 1
    
    for key in total_count:
        table.add_row([key, "% Concentrated", 100.0 * float(concentrated[key])/ float(total_count[key])])
    return table

def get_four_firm_stat_table(timeseries):
    """Extracts a number of metrics related to 4-Firm Concn Ratio"""

    table = PrettyTable()
    table.field_names = ["Metric","Label", "Value"]

    MODERATELY_CONCENTRATED = 50
    HIGHLY_CONCENTRATED = 0.8
    total_count = {}
    moderately = {}
    highly = {}
    for t in timeseries:
        for key in timeseries[t]:
            if 'four_firm' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                moderately[key] = 0 if key not in moderately else moderately[key]
                highly[key] = 0 if key not in highly else highly[key]
                if timeseries[t][key] > HIGHLY_CONCENTRATED:
                    highly[key] += 1
                elif timeseries[t][key] > MODERATELY_CONCENTRATED:
                    moderately[key] += 1
    
    for key in total_count:
        table.add_row([key, "% Highly", 100.0 * float(highly[key])/ float(total_count[key])])
        table.add_row([key, "% Moderately", 100.0 * float(moderately[key])/ float(total_count[key])])
      
    return table

def get_rsi_stat_table(timeseries):
    """Extracts a number of metrics related to RSI"""

    table = PrettyTable()
    table.field_names = ["Metric","Label", "Value"]

    THRESHOLD = 1
    total_count = {}
    under_threshold = {}
    
    for t in timeseries:
        for key in timeseries[t]:
            if 'minimum_rsi' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                under_threshold[key] = 0 if key not in under_threshold else under_threshold[key]
                if timeseries[t][key] < THRESHOLD:
                    under_threshold[key] += 1
                
    
    for key in total_count:
        table.add_row([key, "% Under", 100.0 * float(under_threshold[key])/ float(total_count[key])])
    return table

def get_nersi_stat_table(timeseries):
    """Extracts a number of metrics related to NERSI"""

    table = PrettyTable()
    table.field_names = ["Metric","Label", "Value"]

    THRESHOLD = 1
    total_count = {}
    under_threshold = {}
    
    for t in timeseries:
        for key in timeseries[t]:
            if 'minimum_nersi' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                under_threshold[key] = 0 if key not in under_threshold else under_threshold[key]
                if timeseries[t][key] < THRESHOLD:
                    under_threshold[key] += 1
                
    
    for key in total_count:
        table.add_row([key, "% Under", 100.0 * float(under_threshold[key])/ float(total_count[key])])
    return table

def get_psi_stat_table(timeseries):
    """Extracts a number of metrics related to PSI"""

    table = PrettyTable()
    table.field_names = ["Metric","Label", "Value"]

    total_count = {}
    some_over = {}
    
    for t in timeseries:
        for key in timeseries[t]:
            if 'sum_psi' in key:
                total_count[key] = 1 if key not in total_count else total_count[key] + 1
                some_over[key] = 0 if key not in some_over else some_over[key]
                if timeseries[t][key] > 0:
                    some_over[key] += 1
                
    
    for key in total_count:
        table.add_row([key, "% w/ PSI", 100.0 * float(some_over[key])/ float(total_count[key])])
    return table

def plot_data(timeseries):

    correlation_table = PrettyTable()
    correlation_table.field_names = ["X","Y", "Correlation", "P-Value"]
    

    
    

    def datetime(x):
        return np.array(x, dtype=np.datetime64)

    chart_pairs = [
        # ('hhi_bids', 'weighted_average_price'),
        # ('four_firm_concentration_ratio_bids', 'weighted_average_price'),
        ('hhi_dispatch_ALL', 'weighted_average_price'),
        ('entropy_dispatch_ALL', 'weighted_average_price'),
        ('four_firm_concentration_ratio_dispatch_ALL', 'weighted_average_price'),
        ('average_rsi_ALL', 'weighted_average_price'),
        ('minimum_rsi_ALL', 'weighted_average_price'),
        ('sum_psi_ALL', 'weighted_average_price'),
    ]

    for state in STATES:
        if state != 'ALL':
            chart_pairs.append(['minimum_rsi_'+state, 'price_'+state])
            chart_pairs.append(['minimum_nersi_'+state, 'price_'+state])
            chart_pairs.append(['hhi_bids_'+state, 'price_'+state])
            chart_pairs.append(['hhi_dispatch_'+state, 'price_'+state])
            chart_pairs.append(['entropy_bids_'+state, 'price_'+state])
            chart_pairs.append(['entropy_dispatch_'+state, 'price_'+state])
            # chart_pairs.append(['average_nersi_'+state, 'price_'+state])


    
                   

    variables = {
        # 'demand_ALL':[],
        # 'weighted_average_price':[],
        # 'nsw_demand':[],
        # 'vic_demand':[],
        # 'sa_demand':[],
        # 'qld_demand':[],
        # 'nsw_price':[],
        # 'vic_price':[],
        # 'sa_price':[],
        # 'qld_price':[],
        # 'hhi_bids':[],
        # 'four_firm_concentration_ratio_bids':[],
        # 'hhi_dispatch':[],
        # 'four_firm_concentration_ratio_dispatch':[],
    }

    # Assemble timeseries into arrays of values. 
    # First get a list of all keys. This is important as some gens enter the market late in the timeseries and without this, you end up with funky timeseries lengths. 
    all_keys = []
    for time in sorted(timeseries.keys()):
        for key in timeseries[time]:
            if key not in all_keys:
                all_keys.append(key)
    # Now do the actual assemblaging into lists. 
    for time in sorted(timeseries.keys()):
        for key in all_keys:
            variables[key] = [] if key not in variables else variables[key]
            if key in timeseries[time]:
                variables[key].append(timeseries[time][key])
            else:
                variables[key].append(None)
    
    plots = []

    for key in all_keys:
        print("Key: ", key)

    for key in all_keys:
        if '_nersi_' in key and 'average' not in key and 'minimum' not in key:
            m = re.search(r'(.*)_nersi_(\w+)', key)
            firm = m.group(1)
            state = m.group(2)
            
            chart_pairs.append([key, firm+'_weighted_offer_price_'+state])

    # for state in STATES:
    #     if state != 'ALL':
    #         run_random_forest_price(timeseries, all_keys, state)

    # timeseries_chart = figure(x_axis_type="datetime", title="Spot Bids")
    # timeseries_chart.y_range = Range1d(start=0, end=1)
    # timeseries_chart.extra_y_ranges = {"price": Range1d(start=0, end=200)}
    # timeseries_chart.grid.grid_line_alpha=0.3
    # timeseries_chart.xaxis.axis_label = 'Date'
    # timeseries_chart.yaxis.axis_label = 'Price'

    # # participant_meta = ParticipantService().participant_metadata
    # for i, metric in enumerate(indices.keys()):
    #     if metric not in ['weighted_average_price', 'demand_ALL', 'srmc_qgram', 'lrmc_qgram']:
    #         print(metric)
    #         color = palette.hex_colors[i % len(palette.hex_colors)]
    #         timeseries_chart.line(datetime(sorted(timeseries.keys())), indices[metric], color=color, legend=metric)

    # timeseries_chart.legend.location = "top_left"


    # plots.append(timeseries_chart)

    

    # X/Y Scatter charts based on chart_pairs
    for pair in chart_pairs:
        # get rid of Nones - no good for pearson correlation calc. 
        x_series = []
        y_series = []
        for i in range(len(variables[pair[0]])):
            # if pair[0] in variables and pair[1] in variables:
            if variables[pair[0]][i] and variables[pair[1]][i]:
                x_series.append(variables[pair[0]][i])
                y_series.append(variables[pair[1]][i])
        new_plot = figure(title=pair[0] + " as a function of " + pair[1])
        new_plot.xaxis.axis_label=pair[0]
        new_plot.yaxis.axis_label=pair[1]
        new_plot.circle(x_series, y_series)
        plots.append([new_plot])
        # print("\n")
        
        if len(x_series) > 2:
            correlation = pearsonr(x_series, y_series)
            # print(pair[0]," Pearson Correlation with ",pair[1], correlation)
            correlation_table.add_row([pair[0], pair[1], correlation[0], correlation[1]])
        else:
            pass
            # print("Not enough data points to calculate pearson correlation between ", pair[0],'and', pair[1])
        # print("\n")
    
    # X/Y Scatter with residual supplier inidces of all firms. 
    for state in STATES:
        residual_scatter = figure(title=state+" Firm Residual Supply Index as a function of Total Demand")
        i = 0
        for variable in variables:
            # Start a new chart if this one is full. 
            if i == 20:
                i = 0
                plots.append([residual_scatter])
                residual_scatter = figure(title=state+" Firm Residual Supply Index as a function of Total Demand")
            # Add data set to chart
            if '_rsi_'+state in variable and 'average_rsi' not in variable:
                color = palette.hex_colors[i % len(palette.hex_colors)]
                residual_scatter.circle(variables['demand_'+state], variables[variable], color=color, legend=variable.replace('_rsi_'+state, ''))
                i+= 1
            
        plots.append([residual_scatter])

    # X/Y Scatter with network-augmented residual supplier inidces of all firms. 
    for state in STATES:
        if state != 'ALL':
            residual_scatter = figure(title=state+" Network-Extended Firm Residual Supply Index as a function of Total Demand")
            i = 0
            for variable in variables:
                # Start a new chart if this one is full. 
                if i == 20:
                    i = 0
                    plots.append([residual_scatter])
                    residual_scatter = figure(title=state+" Network Extended Firm Residual Supply Index as a function of Total Demand")
                # Add data set to chart
                if 'minimum_nersi_'+state in variable and 'average_nersi' not in variable:
                    color = palette.hex_colors[i % len(palette.hex_colors)]
                    residual_scatter.circle(variables['demand_'+state], variables[variable], color=color, legend=variable.replace('_nersi_'+state, ''))
                    i+= 1
            plots.append([residual_scatter])
    
    print(correlation_table)
    show(gridplot(plots, plot_width=1200, plot_height=600))  # open a browser

    

def table_data(timeseries):
    hhi_table = get_hhi_stat_table(timeseries)
    entropy_table = get_entropy_stat_table(timeseries)
    four_firm_table = get_four_firm_stat_table(timeseries)
    psi_table = get_psi_stat_table(timeseries)
    rsi_table = get_rsi_stat_table(timeseries)
    nersi_table = get_nersi_stat_table(timeseries)
    print(hhi_table)
    print(entropy_table)
    print(four_firm_table)
    print(psi_table)
    print(rsi_table)
    print(nersi_table)


if __name__=="__main__":
    start_date = pendulum.datetime(2018,1,1,12)
    end_date = pendulum.datetime(2018,1,10,12)
    timeseries = process(start_date, end_date)
    print([key for key in timeseries])
    plot_data(timeseries)
    table_data(timeseries)