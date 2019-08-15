from application.model.bidstack import BidStack
from application.model.participants import ParticipantService
from application.util.interpolation_timeseries import InterpolationTimeseries

from scipy.stats.stats import pearsonr

import os
import csv
import pendulum
import numpy as np

from bokeh.layouts import column, gridplot
from bokeh.plotting import figure, show, output_file
from bokeh.models import LinearAxis, Range1d

from palettable.matplotlib import Plasma_6 as palette

participant_service = ParticipantService()

from application.model.demand import Demand
from application.model.price import Price
# from similarity.normalized_levenshtein import NormalizedLevenshtein

# normalized_levenshtein = NormalizedLevenshtein()

from similarity.qgram import QGram

qgram = QGram(2)




def process_bidstacks(start_date, end_date):
    print("Processing Bidstacks")
    # Get bidstacks for every time period. 
    request = BidStack.objects(trading_period__gte=start_date, trading_period__lte=end_date).fields(trading_period=1, id=1)
    print('Retrieved Bidstacks')

    i = 0
    timeseries = {}

    for bidstack in request:
        # Get the trading period label. 
        dt = pendulum.instance(bidstack.trading_period)
        
        # if(dt.hour == 12 and dt.minute == 0 and dt.day %5 == 0):
        # Filter based on hour so we don't process tonnes of them
        if(dt.hour in [0,6,12,18,24] and dt.minute == 0):
            print(dt)
            # Grab the bids and order in economic dispatch order. 
            bidstack = BidStack.objects.get(id=bidstack.id)
            simple_bids, srmc_bids, lrmc_bids = settle(bidstack)
            # print("Got bid stacks.")
            
            # Grab demand data. 
            demand_req = Demand.objects(date_time=dt)
            regional_demand = {d.region:d.demand for d in demand_req}
            total_demand = int(float(sum([regional_demand[region] for region in regional_demand])))
            

            # Grab price data
            price_req = Price.objects(date_time = dt, price_type='AEMO_SPOT')
            regional_prices = {p.region: p.price for p in price_req}
            weighted_average_price = float(sum([regional_prices[p] * regional_demand[p] for p in regional_prices])) / float(total_demand)

            # Get a dict of all the market shares for this time period
            generator_shares = get_generator_market_shares(bidstack)

            # Grab the representative strings. 
            hhi = get_hhi(generator_shares)
            four_firm_concentraition_ratio = get_four_firm_concentration_ratio(generator_shares)
            # bids_string = get_representative_string(simple_bids, total_demand)
            # srmc_string = get_representative_string(srmc_bids, total_demand)
            # lrmc_string = get_representative_string(lrmc_bids, total_demand)
            # print("Got Representative Strings")
            

            metrics = {
                'hhi': hhi,
                'four_firm_concentration_ratio':four_firm_concentraition_ratio,
                # 'srmc_string_comp': compare_representative_strings(bids_string, srmc_string),
                # 'lrmc_string_comp': compare_representative_strings(bids_string, lrmc_string),
                # 'srmc_fraction_MWh_different': get_fraction_MWh_different(bids_string, srmc_string, total_demand),
                # 'lrmc_fraction_MWh_different': get_fraction_MWh_different(bids_string, lrmc_string, total_demand),
                'datetime': dt,
                'price': regional_prices,
                'weighted_average_price': weighted_average_price,
                'total_demand':total_demand,
                'regional_demand':regional_demand,
                'strike':{
                    'simple': get_strike_price(simple_bids, total_demand),
                    'srmc':get_strike_price(srmc_bids, total_demand),
                    'lrmc': get_strike_price(lrmc_bids, total_demand),
                }
            }
            timeseries[dt] = metrics

             
    print("Finished Processing Bidstack")
    return timeseries


def get_generator_market_shares(bidstack):
    """Gets the market share of each participant. At the moment this is on a generator basis. Need to make a version that gets it on a firm basis - thats the real bullseye here. """
    participants = bidstack.getParticipants()
    shares = {}
    total_volume = 0

    for participant in participants:
        if "RT_" not in participant:
            bid = bidstack.getBid(participant) 
            for band in range(1,9):
                volume = bid.get_volume(band)
                total_volume += volume
                shares[participant] = volume if not participant in shares else shares[participant] + volume
    # Divide all by total volume to get the share rather than gross volume. 
    for participant in shares:
        shares[participant] = float(shares[participant]) / float(total_volume)
    return shares
    
def get_hhi(shares):
    """HHI is the sum of the squares of all the firms in a market. The higher the HHI, the more highly concentrated the market."""
    hhi = sum([shares[p] * shares[p] for p in shares])
    return hhi

def get_four_firm_concentration_ratio(shares):
    """Four firm concentration ratio is the sum of the four biggest market shares"""
    share_list = [shares[p] for p in shares]
    share_list = sorted(share_list, reverse=True)
    top_four = share_list[:4]
    return sum(top_four)

def get_residual_supply_indices(bidstack, total_demand):
    """The Residual Supply Index (RSI) is the ratio of the total capacity of all the other generators in the market to the total market demand at a point in time. """
    participants = bidstack.getParticipants()
    volumes = {}
    rsi = {}
    total_volume = 0

    for participant in participants:
        if "RT_" not in participant:
            bid = bidstack.getBid(participant) 
            for band in range(1,9):
                volume = bid.get_volume(band)
                total_volume += volume
                volumes[participant] = volume if not participant in volumes else volumes[participant] + volume
    # Divide all by total volume to get the share rather than gross volume. 
    for participant in volumes:
        rsi[participant] = float(total_volume - volume[participant]) / float(total_demand)
    return rsi


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

    # print(simple_bids)
    # print(srmc_bids)
    # print(lrmc_bids)
    # simple_bids_string = get_representative_string(simple_bids)
    # srmc_bids_string = get_representative_string(srmc_bids)
    # lrmc_bids_string = get_representative_string(lrmc_bids)
    return simple_bids, srmc_bids, lrmc_bids



def get_strike_price(bids, demand):
    cumulative_demand = 0
    for bid in bids:
        cumulative_demand += bid['volume']
        if cumulative_demand > demand:
        
            return bid['price']
    return 14000


def plot_data(timeseries):


    def datetime(x):
        return np.array(x, dtype=np.datetime64)

    
    plottable = {
        # 'srmc_qgram':[],
        # 'lrmc_qgram':[],
        # 'srmc_fraction_MWh_different':[],
        # 'lrmc_fraction_MWh_different':[],
        'hhi':[],
        'four_firm_concentration_ratio':[],
        'weighted_average_price':[],
        'total_demand':[],
    }

    scatter = {
        'total_demand':[],
        'weighted_average_price':[],
        'nsw_demand':[],
        'vic_demand':[],
        'sa_demand':[],
        'qld_demand':[],
        'nsw_price':[],
        'vic_price':[],
        'sa_price':[],
        'qld_price':[],
        
    }

    strike_comparison = {
        # 'simple':[],
        # 'srmc':[],
        # 'lrmc':[],
        'weighted_average_price':[],
    }

    for time in sorted(timeseries.keys()):
        
        # plottable['srmc_qgram'].append(timeseries[time]['srmc_string_comp']['normalized_qgram'])
        # plottable['lrmc_qgram'].append(timeseries[time]['lrmc_string_comp']['normalized_qgram'])
        # plottable['srmc_fraction_MWh_different'].append(timeseries[time]['srmc_fraction_MWh_different'])
        # plottable['lrmc_fraction_MWh_different'].append(timeseries[time]['lrmc_fraction_MWh_different'])
        plottable['hhi'].append(timeseries[time]['hhi'])
        plottable['four_firm_concentration_ratio'].append(timeseries[time]['four_firm_concentration_ratio'])
        plottable['weighted_average_price'].append(timeseries[time]['weighted_average_price'])
        plottable['total_demand'].append(timeseries[time]['total_demand'])

        scatter['weighted_average_price'].append(timeseries[time]['weighted_average_price'])
        scatter['total_demand'].append(timeseries[time]['total_demand'])

        scatter['nsw_demand'].append(timeseries[time]['regional_demand']['NSW'])
        scatter['vic_demand'].append(timeseries[time]['regional_demand']['VIC'])
        scatter['sa_demand'].append(timeseries[time]['regional_demand']['SA'])
        scatter['qld_demand'].append(timeseries[time]['regional_demand']['QLD'])

        scatter['nsw_price'].append(timeseries[time]['price']['NSW'])
        scatter['vic_price'].append(timeseries[time]['price']['VIC'])
        scatter['sa_price'].append(timeseries[time]['price']['SA'])
        scatter['qld_price'].append(timeseries[time]['price']['QLD'])
        

        # strike_comparison['simple'].append(timeseries[time]['strike']['simple'])
        # strike_comparison['srmc'].append(timeseries[time]['strike']['srmc'])
        # strike_comparison['lrmc'].append(timeseries[time]['strike']['lrmc'])
        strike_comparison['weighted_average_price'].append(timeseries[time]['weighted_average_price'])
            


    p1 = figure(x_axis_type="datetime", title="Spot Bids")
    p1.y_range = Range1d(start=0, end=1)
    p1.extra_y_ranges = {"price": Range1d(start=0, end=200)}
    p1.grid.grid_line_alpha=0.3
    p1.xaxis.axis_label = 'Date'
    p1.yaxis.axis_label = 'Price'

    # participant_meta = ParticipantService().participant_metadata
    for i, metric in enumerate(plottable.keys()):
        if metric not in ['weighted_average_price', 'total_demand', 'srmc_qgram', 'lrmc_qgram']:
            print(metric)
            color = palette.hex_colors[i % len(palette.hex_colors)]
            p1.line(datetime(sorted(timeseries.keys())), plottable[metric], color=color, legend=metric)
    # p1.line(datetime(sorted(timeseries.keys())), lgc_prices, legend="LGC Price", line_width = 2,  line_dash='dashed')
    # p1.line(datetime(sorted(timeseries.keys())), plottable['weighted_average_price'], color="blue",line_width = 2,  line_dash='dashed', y_range_name="price")
    # p1.add_layout(LinearAxis(y_range_name="price"), 'left')
    p1.legend.location = "top_left"




    p2 = figure(x_axis_type="datetime", title="Spot Market Prices")
    p2.grid.grid_line_alpha=0.3
    p2.xaxis.axis_label = 'Date'
    p2.yaxis.axis_label = 'Strike Price'
    for i, metric in enumerate(strike_comparison.keys()):
            color = palette.hex_colors[i % len(palette.hex_colors)]
            p2.line(datetime(sorted(timeseries.keys())), strike_comparison[metric], color=color, legend=metric)
    
    p2.legend.location = "top_left"

    # p3 = figure(title="LRMC Fraction vs Spot Price (Scatter)")
    # p3.xaxis.axis_label="LRMC Fraction"
    # p3.yaxis.axis_label="Weighted Average Spot Price"
    # p3.circle(plottable['lrmc_fraction_MWh_different'], plottable['weighted_average_price'])

    # p4 = figure(title="LRMC Fraction vs Demand (Scatter)")
    # p4.xaxis.axis_label="LRMC Fraction"
    # p4.yaxis.axis_label="Demand"
    # p4.circle(plottable['lrmc_fraction_MWh_different'], plottable['total_demand'])

    # p5 = figure(title="SRMC Fraction vs Spot Price (Scatter)")
    # p5.xaxis.axis_label="SRMC Fraction"
    # p5.yaxis.axis_label="Weighted Average Spot Price"
    # p5.circle(plottable['srmc_fraction_MWh_different'], plottable['weighted_average_price'])

    # p6 = figure(title="SRMC Fraction vs Demand (Scatter)")
    # p6.xaxis.axis_label="SRMC Fraction"
    # p6.yaxis.axis_label="Demand"
    # p6.circle(plottable['srmc_fraction_MWh_different'], plottable['total_demand'])

   

    plots = [[p1], [p2]]

    for key in scatter:
        hhi = figure(title="HHI vs "+key)
        hhi.xaxis.axis_label="HHI"
        hhi.yaxis.axis_label=key
        hhi.circle( scatter[key], plottable['hhi'])

        four_firm = figure(title="Four Firm Concentration Index vs "+key)
        four_firm.xaxis.axis_label="Four Firm Concentration Index"
        four_firm.yaxis.axis_label=key
        four_firm.circle(scatter[key], plottable['four_firm_concentration_ratio'])

        plots.append([hhi])
        plots.append([four_firm])
        # plots.append([srmc_qgram_scatter])
        # plots.append([lrmc_qgram_scatter])

        print("\n")
        print("HHI Pearson Correlation with "+key, pearsonr(scatter[key], plottable['hhi']))
        print("Four Firm Concentration Ratio Pearson Correlation with "+key, pearsonr(scatter[key], plottable['four_firm_concentration_ratio']))
        
        print("\n")
    
    
    
    # print("\n\nTotals:")
    # print("SRMC Q-Gram Pearson Correlation with Price", pearsonr(plottable['srmc_qgram'],plottable['weighted_average_price']))
    # print("LRMC Q-Gram Pearson Correlation with Price", pearsonr(plottable['lrmc_qgram'],plottable['weighted_average_price']))
    # print("SRMC Fraction MWh Different Pearson Correlation with Price", pearsonr(plottable['srmc_fraction_MWh_different'],plottable['weighted_average_price']))
    # print("LRMC Fraction MWh Different Pearson Correlation with Price", pearsonr(plottable['lrmc_fraction_MWh_different'],plottable['weighted_average_price']))

    # print("SRMC Q-Gram Pearson Correlation with Demand", pearsonr(plottable['srmc_qgram'],plottable['total_demand']))
    # print("LRMC Q-Gram Pearson Correlation with Demand", pearsonr(plottable['lrmc_qgram'],plottable['total_demand']))
    # print("SRMC Fraction MWh Different Pearson Correlation with Demand", pearsonr(plottable['srmc_fraction_MWh_different'],plottable['total_demand']))
    # print("LRMC Fraction MWh Different Pearson Correlation with Demand", pearsonr(plottable['lrmc_fraction_MWh_different'],plottable['total_demand']))

    show(gridplot(plots, plot_width=1200, plot_height=500))  # open a browser

if __name__=="__main__":
    start_date = pendulum.datetime(2018,1,1,12)
    end_date = pendulum.datetime(2018,12,30,12)
    timeseries = process_bidstacks(start_date, end_date)
    plot_data(timeseries)