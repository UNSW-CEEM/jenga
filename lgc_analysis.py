from application.model.bidstack import BidStack
from application.model.participants import ParticipantService
from application.util.interpolation_timeseries import InterpolationTimeseries
import os
import csv
import pendulum
import numpy as np

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file
from palettable.matplotlib import Plasma_6 as palette


def load_lgc_data():
    ts = InterpolationTimeseries()
    print("Loading LGC Data")
    # with open(os.path.join('lgc', 'lgc_prices.csv')) as f:
    with open(os.path.join('lgc', 'lgc_prices_2018_only.csv')) as f:
        reader = csv.DictReader(f)
        reader = list(reader)
        for i, line in enumerate(reader):
            ts.add(pendulum.parse(line['date']), {'price': line['price']})
            if i%100 == 0:
                print("Loaded LGC Data", i, "of", len(reader))
            # print(line)
    print("Finished Loading LGC Data")
    return ts

def process_bidstacks():
    print("Processing Bidstacks")
    request = BidStack.objects().fields(trading_period=1, id=1)
    print('Retrieved Bidstacks')

    PRICE_MIN = -300
    PRICE_MAX = -10


    i = 0
    timeseries = {}
    relevant_bidders = []

    for bidstack in request:
        # Get the trading period label. 
        dt = pendulum.instance(bidstack.trading_period)
        
        if(dt.hour == 12 and dt.minute == 0 and dt.day %5 == 0):
            bidstack = BidStack.objects.get(id=bidstack.id)
            print("Processing Bidstack", dt)
            participants = bidstack.getParticipants()
            for participant in participants:
                # Get some relevant data about the participant. 
                # tech_type = participant_meta[participant]['technology_type_primary'] if participant in participant_meta else None
                # fuel_source_descriptor = participant_meta[participant]['fuel_source_descriptor'] if participant in participant_meta else None
                # fuel_source_primary = participant_meta[participant]['fuel_source_primary'] if participant in participant_meta else None


                # Look at the participant's bids - see if any fall within the range we are interested in. 
                # print(participant)
                bid = bidstack.getBid(participant)
                for band in range(1,9):
                    price = bid.get_price(band)
                    volume = bid.get_volume(band)
                    if volume > 0 and price >= PRICE_MIN and price <= PRICE_MAX:
                        # If we haven't seen this participant before, add them to the list. 
                        if participant not in relevant_bidders:
                            relevant_bidders.append(participant)
                        # Add the data point to the timeseries
                        timeseries[dt] = {} if not dt in timeseries else timeseries[dt]
                        timeseries[dt][participant] = price
                        
                        # print(participant, band, bid.get_price(band), bid.get_volume(band), tech_type, fuel_source_descriptor, fuel_source_primary)


                # In future runs, could use these to narrow down. Leave it for the moment. 
                
                # print(tech_type, fuel_source_descriptor, fuel_source_primary)
            # break   
        # if i == 5:
        #     break
        # i += 1
    print("Finished Processing Bidstack")
    return timeseries, relevant_bidders

def plot_data(timeseries, relevant_bidders, lgc_data):
    

    
    
    # from bokeh.sampledata.stocks import AAPL

    def datetime(x):
        return np.array(x, dtype=np.datetime64)

    plottable = {p:[] for p in relevant_bidders}
    lgc_prices = []
    for time in sorted(timeseries.keys()):
        for participant in relevant_bidders:
            if participant in timeseries[time]:
                plottable[participant].append(timeseries[time][participant])
            else:
                plottable[participant].append(float("nan"))
        
        lgc_prices.append(-1.0 * lgc_data.get(time, 'price'))


    p1 = figure(x_axis_type="datetime", title="Spot Bids")
    p1.grid.grid_line_alpha=0.3
    p1.xaxis.axis_label = 'Date'
    p1.yaxis.axis_label = 'Price'

    # participant_meta = ParticipantService().participant_metadata
    for i, participant in enumerate(relevant_bidders):
        fuel_source_primary = ParticipantService().participant_metadata[participant]['fuel_source_primary'] if participant in ParticipantService().participant_metadata else ""
        # Get rid of irrelevant gen types. 
        if fuel_source_primary not in ["Hydro", "Fossil"]:
            color = palette.hex_colors[i % len(palette.hex_colors)]
            p1.line(datetime(sorted(timeseries.keys())), plottable[participant], color=color, legend=participant + " "+ fuel_source_primary)
    p1.line(datetime(sorted(timeseries.keys())), lgc_prices, legend="LGC Price", line_width = 2,  line_dash='dashed')

    p1.legend.location = "top_left"

    window_size = 30


    show(gridplot([[p1]], plot_width=1200, plot_height=500))  # open a browser

if __name__=="__main__":
    lgc_data = load_lgc_data()
    timeseries, relevant_bidders = process_bidstacks()
    plot_data(timeseries, relevant_bidders, lgc_data)