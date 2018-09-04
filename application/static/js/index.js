console.log('Gday mate');




Vue.component('price-chart',{
    template:`
        <div class="price-chart">
            <h1>Price Chart</h1>
            <div class="ct-chart" id="prices"></div>
        </div>
    `,
    mounted(){

          $.getJSON('/prices/NSW/1522987200/1525579200', function(result){
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
                        zoomType: 'x'
                    },
                    title: {
                        text: 'Pool Price Timeseries'
                    },
                    subtitle: {
                        text: document.ontouchstart === undefined ?
                                'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
                    },
                    xAxis: {
                        type: 'datetime',
                    },
                    yAxis: {
                        title: {
                            text: 'Price $/MWh'
                        }
                    },
                    legend: {
                        enabled: false
                    },
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
        
                    series: [{
                        type: 'area',
                        name: 'Spot Price',
                        data: result.spot.prices
                    }]
                });
          });
        }
});

Vue.component('stack-explorer',{
    template:`
        <div>
            <h1>Stack Explorer</h1>

            <select>
                <option v-for="date in dates" value="volvo" v-on:click="select_bidstack(date)">{{date_to_str(date)}}</option>
            </select> 

            <div class="container" id="container"></div>
            
            <div v-for="bid in bidstack">
                {{bid}}
            </div>

        </div>
    `,
    data(){
        return{
            dates:[],
            bidstack : [],
            mode:'participant',
        }
    },
    methods:{
        date_to_str(date_iso){
            return moment.unix(date_iso).format('YYYY MMM DD HH:mm');
        },

        select_bidstack(date_iso){
            console.log('Selecting bidstack', date_iso);
            var self = this;
            $.getJSON('/bidstack/'+date_iso, function(response){
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
                    text: 'All Bids'
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
                            pointFormat: '{point.x} MWh, {point.y} $/MWh'
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