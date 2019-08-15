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
    request = BidStack.objects(trading_period__gte=start_date, trading_period__lte=end_date).fields(trading_period=1, id=1)
    print('Retrieved Bidstacks')

    i = 0
    timeseries = {}

    for bidstack in request:
        # Get the trading period label. 
        dt = pendulum.instance(bidstack.trading_period)
        
        # if(dt.hour == 12 and dt.minute == 0 and dt.day %5 == 0):
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

            # Grab the representative strings. 
            bids_string = get_representative_string(simple_bids, total_demand)
            srmc_string = get_representative_string(srmc_bids, total_demand)
            lrmc_string = get_representative_string(lrmc_bids, total_demand)
            # print("Got Representative Strings")

            metrics = {
                'srmc_string_comp': compare_representative_strings(bids_string, srmc_string),
                'lrmc_string_comp': compare_representative_strings(bids_string, lrmc_string),
                'srmc_fraction_MWh_different': get_fraction_MWh_different(bids_string, srmc_string, total_demand),
                'lrmc_fraction_MWh_different': get_fraction_MWh_different(bids_string, lrmc_string, total_demand),
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


def get_representative_string(bids, demand_limit=None):
    indices = []
    output_string = ""
    # Create an array of the participant indices for each MWh of bidding
    for bid in bids:
        index = participant_service.get_index(bid['participant'])
        for i in range(int(bid['volume'])):
            indices.append(index)
    
    # Trim to a given demand if required. 
    if demand_limit:
        indices = indices[:demand_limit]

    # Convert to unicode string. 
    for index in indices:
        if index:
            output_string += chr(index+97)
        else:
            output_string += chr(5000)
    return output_string

def compare_representative_strings(str1, str2):
    # print("Comparing Representative Strings")
    qgram_dist = qgram.distance(str1, str2)
    return {
            'qgram':qgram_dist,
            'normalized_qgram' : float(qgram_dist) / float(max(len(str1), len(str2))),
            
        }

def get_fraction_MWh_different(str1, str2, demand):
    counter_bs_1 = {}
    counter_bs_2 = {}
    for i in range(min(len(str1), len(str2), demand)):
        
        gen_1_id = str1[i]
        gen_2_id = str2[i]
        counter_bs_1[gen_1_id] = 0 if not gen_1_id in counter_bs_1 else counter_bs_1[gen_1_id] + 1
        counter_bs_2[gen_2_id] = 0 if not gen_2_id in counter_bs_2 else counter_bs_2[gen_2_id] + 1
    
    total_different = 0
    for gen_id in counter_bs_1:
        total_different += abs(counter_bs_1[gen_id] - counter_bs_2[gen_id]) if gen_id in counter_bs_2 else counter_bs_1[gen_id]
        
    # total_different = float(total_different) / 2.0
    fraction = float(total_different) / float(demand)
    # print(fraction, total_different, demand)
    return fraction
        


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
        'srmc_qgram':[],
        'lrmc_qgram':[],
        'srmc_fraction_MWh_different':[],
        'lrmc_fraction_MWh_different':[],
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
        'srmc':[],
        'lrmc':[],
        'weighted_average_price':[],
    }

    for time in sorted(timeseries.keys()):
        
        plottable['srmc_qgram'].append(timeseries[time]['srmc_string_comp']['normalized_qgram'])
        plottable['lrmc_qgram'].append(timeseries[time]['lrmc_string_comp']['normalized_qgram'])
        plottable['srmc_fraction_MWh_different'].append(timeseries[time]['srmc_fraction_MWh_different'])
        plottable['lrmc_fraction_MWh_different'].append(timeseries[time]['lrmc_fraction_MWh_different'])
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
        strike_comparison['srmc'].append(timeseries[time]['strike']['srmc'])
        strike_comparison['lrmc'].append(timeseries[time]['strike']['lrmc'])
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
        srmc_scatter = figure(title="SRMC Fraction vs "+key)
        srmc_scatter.xaxis.axis_label="SRMC Fraction"
        srmc_scatter.yaxis.axis_label=key
        srmc_scatter.circle( scatter[key], plottable['srmc_fraction_MWh_different'])

        lrmc_scatter = figure(title="LRMC Fraction vs "+key)
        lrmc_scatter.xaxis.axis_label="LRMC Fraction"
        lrmc_scatter.yaxis.axis_label=key
        lrmc_scatter.circle(scatter[key], plottable['lrmc_fraction_MWh_different'])

        srmc_qgram_scatter = figure(title="SRMC Q-Gram Distance vs "+key)
        srmc_qgram_scatter.xaxis.axis_label="SRMC Q-Gram Distance"
        srmc_qgram_scatter.yaxis.axis_label=key
        srmc_qgram_scatter.circle(scatter[key], plottable['srmc_qgram'])

        lrmc_qgram_scatter = figure(title="LRMC Q-Gram Distance vs "+key)
        lrmc_qgram_scatter.xaxis.axis_label="LRMC Q-Gram Distance"
        lrmc_qgram_scatter.yaxis.axis_label=key
        lrmc_qgram_scatter.circle( scatter[key], plottable['lrmc_qgram'])

        plots.append([srmc_scatter])
        plots.append([lrmc_scatter])
        plots.append([srmc_qgram_scatter])
        plots.append([lrmc_qgram_scatter])

        print("\n")
        print("SRMC Fraction MWh Different Pearson Correlation with "+key, pearsonr(scatter[key], plottable['srmc_fraction_MWh_different']))
        print("LRMC Fraction MWh Different Pearson Correlation with "+key, pearsonr(scatter[key], plottable['lrmc_fraction_MWh_different']))
        print("SRMC Q-Gram Pearson Correlation with "+key, pearsonr(scatter[key],plottable['srmc_qgram']))
        print("LRMC Q-Gram Pearson Correlation with "+key, pearsonr(scatter[key],plottable['lrmc_qgram']))
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