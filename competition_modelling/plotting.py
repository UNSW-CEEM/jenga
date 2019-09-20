
from bokeh.layouts import column, gridplot
from bokeh.plotting import figure, show, output_file
from bokeh.models import LinearAxis, Range1d

from palettable.matplotlib import Plasma_20 as palette
from prettytable import PrettyTable
import re
from scipy.stats.stats import pearsonr
from . import config

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

    for state in config.STATES:
        if state != 'ALL':
            chart_pairs.append(['minimum_rsi_'+state, 'price_'+state])
            chart_pairs.append(['minimum_nersi_'+state, 'price_'+state])
            chart_pairs.append(['hhi_bids_'+state, 'price_'+state])
            chart_pairs.append(['nechhi_'+state, 'price_'+state])
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

    # for state in config.STATES:
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
    for state in config.STATES:
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
    for state in config.STATES:
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

    