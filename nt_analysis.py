
from bokeh.layouts import column, gridplot
from bokeh.plotting import figure, show, output_file
from bokeh.models import LinearAxis, Range1d, ColumnDataSource

from bokeh.palettes import GnBu3, OrRd3

from palettable.matplotlib import Plasma_5 as palette


from simple_markets import northern_territory as grid


def calculate_hhi(generators):
    total_available_capacity = sum([generators[g]['capacity_MW'] for g in generators])
    sum_squares = 0
    for g in generators:
        market_share = 100.0 * float(generators[g]['capacity_MW']) / float(total_available_capacity)
        sum_squares += market_share * market_share
    return sum_squares


def calculate_pivotal_supplier_index(generators, demand):
    
    total_available_capacity = sum([generators[g]['capacity_MW'] for g in generators])
    results = {}
    for g in generators:
        remaining_supply = total_available_capacity - generators[g]['capacity_MW']
        if remaining_supply > demand:
            results[g] = 0
        else:
            results[g] = 1
    return results


def calculate_residual_supply_index(generators, demand):
    total_available_capacity = sum([generators[g]['capacity_MW'] for g in generators])
    results = {}
    for g in generators:
        remaining_supply = total_available_capacity - generators[g]['capacity_MW']
        rsi = 100.0 * remaining_supply / demand
        results[g] = rsi
    return results

if __name__ == "__main__":
    hhi = calculate_hhi(grid.generators)
    print(hhi)

    best_case_psi = calculate_pivotal_supplier_index(grid.generators, grid.MINIMUM_DEMAND_MW)
    average_case_psi = calculate_pivotal_supplier_index(grid.generators, grid.AVERAGE_DEMAND_MW)
    worst_case_psi = calculate_pivotal_supplier_index(grid.generators, grid.PEAK_DEMAND_MW)


    rsi_timeseries = {g:[] for g in grid.generators}
    psi_timeseries = {g:[] for g in grid.generators}
    demand_series = []

    plots = []

    # Build datasets by scaling demand. 
    for demand in range(grid.MINIMUM_DEMAND_MW, grid.PEAK_DEMAND_MW+20):
        if demand % 10 == 0:
            psi = calculate_pivotal_supplier_index(grid.generators, demand)
            rsi = calculate_residual_supply_index(grid.generators, demand)
            print(demand, psi_timeseries['Channel Island'])
            [psi_timeseries[g].append(psi[g]) for g in psi_timeseries]
            [rsi_timeseries[g].append(rsi[g]) for g in rsi_timeseries]
            demand_series.append(demand)
    # print( [ len(psi_timeseries[g]) for g in psi_timeseries ])
    # # print("yo")
    # print( len(demand_series) )
    # Put together the RSI chart
    rsi_chart = figure(title="RSI as a function of Demand")
    rsi_chart.xaxis.axis_label = 'Demand'
    rsi_chart.yaxis.axis_label = 'RSI'
    for i, g in enumerate(rsi_timeseries):
        rsi_chart.line(demand_series, rsi_timeseries[g], color=palette.hex_colors[i % len(palette.hex_colors)],legend=g)
    plots.append([rsi_chart])

    # Put together the PSI chart
    psi_chart = figure(title="PSI as a function of Demand", x_range=[str(d) for d in demand_series],)
    psi_chart.xaxis.axis_label = 'Demand'
    psi_chart.yaxis.axis_label = 'RSI'
    # for i, g in enumerate(rsi_timeseries):
    psi_timeseries['demand'] = demand_series
    print([g for g in grid.generators])
    psi_chart.vbar_stack([g for g in grid.generators], x='demand', width=0.9, source=psi_timeseries, legend=[g for g in grid.generators])
    plots.append([psi_chart])

    show(gridplot(plots, plot_width=1200, plot_height=600))  # open a browser