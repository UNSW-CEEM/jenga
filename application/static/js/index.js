console.log('Gday mate');




Vue.component('price-chart',{
    template:`
        <div class="price-chart">
                <select v-model="state">
                    <option disabled value="">Please select one</option>
                    <option>QLD</option>
                    <option>NSW</option>
                    <option>VIC</option>
                    <option>SA</option>
                    <option>TAS</option>
                </select>
            
            <div class="ct-chart price" id="prices"></div>
        </div>
    `,
    // props:['state'],
    data(){
        return{
            state:'NSW',
        }
    },
    watch:{
        state(){
            this.drawChart();
        }
    },
    
    methods:{
        drawChart(){
            var self = this;
            $.getJSON('/bidstack/dates', function(response){
         
                var start_date = response[0];
                var end_date = response[response.length - 1];
    
                
    
            //   $.getJSON('/prices/NSW/1522987200/1525579200', function(result){
                $.getJSON('/prices/'+self.state+'/'+start_date+'/'+end_date, function(result){
                    console.log('Prices', result);
                    // var data = {
                    //     // A labels array that can contain any sort of values
                    //     // labels: result.spot.dates,
                    //     // Our series array that contains series objects or in this case series data arrays
                    //     series: [
                    //       result.spot.prices
                    //     ]
                    //   };
                      
                      // Create a new line chart object where as first parameter we pass in a selector
                      // that is resolving to our chart container element. The Second parameter
                      // is the actual data object.
                    //   new Chartist.Line('.ct-chart', data);
    
                      Highcharts.chart('prices', {
                        chart: {
                            zoomType: 'xy'
                        },
                        title: {
                            text: 'Pool Price Timeseries '+self.state
                        },
                        subtitle: {
                            text: document.ontouchstart === undefined ?
                                    'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
                        },
                        xAxis: {
                            type: 'datetime',
                        },
                        yAxis: [{
                            title: {
                                text: 'Price $/MWh'
                            }
                        },
                        {
                            title: {
                                text: 'Demand MW'
                            },
                            opposite:true,
                        }],
                        tooltip: {
                            positioner: function() {
                                return {
                                  x: this.chart.plotLeft,
                                  y: this.chart.plotTop - 55,
                                };
                              },
                            shared:true,
                        },
                        legend: {
                            layout: 'vertical',
                            align: 'right',
                            x: -150,
                            verticalAlign: 'top',
                            y: 0,
                            floating: true,
                            backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'
                        },
                        // resetZoomButton: {
                        //     position: {
                        //         // align: 'right', // by default
                        //         // verticalAlign: 'bottom', // by default
                        //         x: -200,
                        //         y: 0,
                        //     }
                        // },
                        plotOptions: {
                            area: {
                                fillColor: {
                                    linearGradient: {
                                        x1: 0,
                                        y1: 0,
                                        x2: 0,
                                        y2: 1
                                    },
                                    stops: [
                                        [0, Highcharts.getOptions().colors[0]],
                                        [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
                                    ]
                                },
                                marker: {
                                    radius: 2
                                },
                                lineWidth: 1,
                                states: {
                                    hover: {
                                        lineWidth: 1
                                    }
                                },
                                threshold: null
                            }
                        },
            
                        series: [
                            {
                                type: 'area',
                                name: 'Spot Price',
                                yaxis: 1,
                                data: result.spot.prices
                            },
                            {
                                type: 'line',
                                name: 'Basic Dispatch Price',
                                yaxis: 1,
                                data: result.basic_dispatch.prices
                            },
                            {
                                type: 'line',
                                name: 'LMP Price',
                                yaxis: 1,
                                data: result.lmp_dispatch.prices
                            },
                            {
                                type: 'line',
                                name: 'Basic VCG Price',
                                yaxis: 1,
                                data: result.basic_vcg_dispatch.prices
                            },
                            {
                                type: 'line',
                                name: 'Basic VCG Price (Min Bid = 0)',
                                yaxis: 1,
                                data: result.basic_vcg_min_bid_zero_dispatch.prices
                            },
                            {
                                type: 'line',
                                name: 'Basic (Min Bid = 0)',
                                yaxis: 1,
                                data: result.basic_min_bid_zero.prices
                            },
                            {
                                type: 'line',
                                name: 'LMP VCG',
                                yaxis: 1,
                                data: result.lmp_vcg_dispatch.prices
                            },
                            {
                                type: 'line',
                                name: 'LMP VCG (Min Bid = 0)',
                                yaxis: 1,
                                data: result.lmp_vcg_min_bid_zero_dispatch.prices
                            },
                            {
                                type: 'line',
                                name: 'Total Industrial Cost',
                                yaxis: 1,
                                data: result.total_industrial_cost.prices
                            },
                            {
                                type: 'line',
                                name: 'Total Industrial Cost (Min Bid Zero)',
                                yaxis: 1,
                                data: result.total_industrial_cost_min_bid_zero.prices
                            },
                            {
                                type: 'line',
                                name: 'Demand',
                                yaxis: 2,
                                data: result.demand.demand
                            }
                        ]
                    });
              });
            });
        }
    },
    mounted(){
        this.drawChart();
    }
});

Vue.component('stack-explorer',{
    template:`
        <div>
            <h1>Stack Explorer</h1>
            <div class="selectors">
                <select>
                    <option v-for="date in dates" value="volvo" v-on:click="select_bidstack(date)">{{date_to_str(date)}}</option>
                </select> 

                <select v-model="state">
                    <option disabled value="">Please select one</option>
                    <option>ALL</option>
                    <option>QLD</option>
                    <option>NSW</option>
                    <option>VIC</option>
                    <option>SA</option>
                    <option>TAS</option>
                </select>
            </div>

            <div class="container" id="container"></div>
            
            

        </div>
    `,
    data(){
        return{
            dates:[],
            bidstack : [],
            mode:'participant',
            state:'NSW',
            date_iso:0,
        }
    },
    watch:{
        state(){
            console.log('state changed to ', this.state);
            this.select_bidstack(this.date_iso)
        }
    },
    methods:{
        date_to_str(date_iso){
            return moment.unix(date_iso).format('YYYY MMM DD HH:mm');
        },

        select_bidstack(date_iso){
            console.log('Selecting bidstack', date_iso);
            this.date_iso = date_iso;
            var self = this;
            $.getJSON('/bidstack/'+this.state+'/'+date_iso, function(response){
                console.log('bidstack', response);
                self.bidstack = response;
                self.draw_chart();
            });

        },
        draw_chart(){

            var series = [];
            //Assemble data
            
            for(var name in this.bidstack){
                var data = [];
                for(var band in this.bidstack[name].bands){
                    if(this.bidstack[name].bands[band].volume > 0){
                        data.push([this.bidstack[name].bands[band].volume, this.bidstack[name].bands[band].price ])
                    }
                }
                series.push({
                    name:name,
                    data:data,
                });
            }

           
        

            Highcharts.chart('container', {
                chart: {
                    type: 'scatter',
                    zoomType: 'xy'
                },
                title: {
                    text: 'All Bids'+this.state
                },
                subtitle: {
                    text: 'Source: AEMO'
                },
                xAxis: {
                    title: {
                        enabled: true,
                        text: 'Volume (MW)'
                    },
                    startOnTick: true,
                    endOnTick: true,
                    showLastLabel: true
                },
                yAxis: {
                    title: {
                        text: 'Price ($/MWh)'
                    }
                },
                legend: {
                    layout: 'vertical',
                    align: 'right',
                    verticalAlign: 'top',
                   
                    floating: true,
                    backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
                    borderWidth: 1
                },
                plotOptions: {
                    scatter: {
                        marker: {
                            radius: 5,
                            states: {
                                hover: {
                                    enabled: true,
                                    lineColor: 'rgb(100,100,100)'
                                }
                            }
                        },
                        states: {
                            hover: {
                                marker: {
                                    enabled: false
                                }
                            }
                        },
                        tooltip: {
                            headerFormat: '<b>{series.name}</b><br>',
                            pointFormat: '{point.x} MWh, {point.y} $/MWh',
                            
                        }
                    }
                },

                series: series,
            });
        }
    },
    mounted(){
        var self = this;
        $.getJSON('/bidstack/dates', function(response){
            console.log('dates', response);
            for(var i = 0; i<response.length; i++){
                self.dates.push(response[i]);
            }
            self.select_bidstack(self.dates[0]);
        });
    }
})


var app = new Vue({
    el:'.content',
    delimiters:['[[',']]'],
    data:{
        hello:'HI THERE'
    },
});