
Vue.component('bidstack',{
    template:`
        <div class="bidstack">
            <div class="header-bar">
                <span class="logo">JENGA | The NEM Bid Stack Explorer</span>
                <span class="selected-date">
                    <span class="timeshift_button" v-on:click="shift_time(-30)"> << </span>
                        {{date_to_str(date_iso)}}
                    <span class="timeshift_button" v-on:click="shift_time(30)"> >> </span>
                
                </span>

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
            

            <div class="ct-chart price" id="spotprices"></div>
            
            
            <div class="columns">
                <div class="y-axis-label">
                <span>Max</span>
                
                <span>Min</span>
                
                </div>
                <div class="column" v-for="(bid, index) in sorted_bidstack" v-on:click="select_bid(bid)" v-bind:style="{ height: get_height_percent(bid.price) + '%', width: get_width_percent(bid.volume) + '%', 'background-color':get_color(bid), transform:get_transform(bid.price)}">
                </div>
            </div>

            <div class="stats-row" >
                <div class="filters">
                    <span class="title">Bidstack Filters</span>

                    <div class="fuel_source_primary_filter">
                        <span class="filter-label">Primary Fuel Source</span>
                        <div class="filter-option" v-for="property in filters['fuel_source_primary']" v-on:click="toggle_filter('fuel_source_primary',property)" v-bind:class="{ 'filter-on': is_filtered('fuel_source_primary',property),'filter-off': !is_filtered('fuel_source_primary',property) }">
                            {{property}} 
                        </div>
                    </div>
                </div>

                <div class="bid-stats" v-if="selected_bid.generator">

                    <span class="title">{{selected_bid.meta.station_name}}</span>
                    <span class="duid">{{selected_bid.generator}}</span>
                    <span class="description">{{selected_bid.meta.label}}</span>
                    <span class="description">{{selected_bid.meta.fuel_source_primary}} | {{selected_bid.meta.fuel_source_descriptor}} </span>
                    <span class="description">{{selected_bid.meta.technology_type_primary}} | {{selected_bid.meta.technology_type_descriptor}} </span>
                    

                    <span>
                        Bid Price: $ {{selected_bid.price}} / MWh
                    </span>
                    
                    <span>
                        Bid Volume: {{selected_bid.volume}} MWh
                    </span>
                   
                </div>
                <div class="bid-stats" v-else >
                    <span class="placeholder">No Bid Selected</span>
                </div>

                <div class="marginal-benefit" v-if="selected_bid.generator">
                    <div class="marginal-benefit-header">
                        <div class="select-marginal-benefit-mode">
                            <div class="select-marginal-benefit-mode-button" v-bind:class="{selected: marginal_benefit_mode=='company'}" v-on:click="select_marginal_benefit_mode('company')" >Company</div>    
                            <div class="select-marginal-benefit-mode-button" v-bind:class="{selected: marginal_benefit_mode=='generator'}" v-on:click="select_marginal_benefit_mode('generator')">Generator</div>
                        </div>
                        <span v-if="marginal_benefit_mode=='company'">{{selected_bid.meta.label}} | Cumulative Marginal Benefit Curve </span>
                        <span v-if="marginal_benefit_mode=='generator'">{{selected_bid.meta.station_name}} | Marginal Benefit Curve </span>
                    </div>
                    <div class="marginal-benefit-curve">
                        <div class="column" v-for="(bid, index) in selected_bid_marginal_benefit_curve" v-on:click="select_bid(bid)" v-bind:style="{ height: get_height_percent(bid.price) + '%', width: get_marginal_benefit_width_percent(bid.volume) + '%', transform:get_transform(bid.price)}"></div>
                    </div>
                </div>
                <div class="marginal-benefit" v-else >
                    <span class="placeholder"> No Bid Selected </span>
                </div>

            </div>
            
        </div>
    `,
    data(){
        return{
            dates:[],
            bidstack : [],
            saved_bidstacks:{
                'QLD':{},
                'NSW':{},
                'VIC':{},
                'SA':{},
                'TAS':{},
                'ALL':{},
            },
            mode:'generator',
            state:'NSW',
            date_iso:0,
            total_volume:100,
            min_price:0,
            max_price:0,
            chart_price_cap:14000,
            chart_price_floor:-10000,
            selected_bid:{meta:{}},
            sorted_bidstack:[],
            colors:{},
            filters:{
                'fuel_source_primary':[],
            },

            marginal_benefit_mode:'company',
            // marginal_benefit_mode:'generator',
    
            selected_filters:{

            }
        }
    },
    watch:{
        state(){
            console.log('state changed to ', this.state);
            this.select_bidstack(this.date_iso)
            this.drawSpot();
        },
        
    },
    computed:{
        selected_bid_marginal_benefit_curve(){
            var selected_bid_marginal_benefit_curve = [];
            for(var i = 0; i< this.sorted_bidstack.length; i++){
                if(this.marginal_benefit_mode=='generator'){
                    if(this.sorted_bidstack[i].meta.station_name == this.selected_bid.meta.station_name){
                        selected_bid_marginal_benefit_curve.push(this.sorted_bidstack[i]);
                    }
                }else if(this.marginal_benefit_mode=='company'){
                    if(this.sorted_bidstack[i].meta.label == this.selected_bid.meta.label){
                        selected_bid_marginal_benefit_curve.push(this.sorted_bidstack[i]);
                    }
                }
            }
            return selected_bid_marginal_benefit_curve;
        },
        marginal_benefit_total_volume(){
            var volume = 0;
            for(var i = 0; i< this.sorted_bidstack.length; i++){
                if(this.sorted_bidstack[i].generator == this.selected_bid.generator){
                    volume += this.sorted_bidstack[i].volume;
                }
            }
            return volume;
        }
        
    },
    methods:{
        select_marginal_benefit_mode(mode){
            console.log('Selecting marginal benefit mode', mode);
            this.marginal_benefit_mode = mode;
        },
        shift_time(minutes){
            console.log('Shifting time by',minutes, 'minutes')
            var new_date_iso = moment.unix(this.date_iso).add(minutes,'minutes').unix();
            this.select_bidstack(new_date_iso);
        },
        toggle_filter(param, value){
            console.log('Toggling filter for ',param, value)
            if(this.is_filtered(param, value)){
                this.remove_filter(param, value);
            }else{
                this.add_filter(param, value);
            }
            
            this.draw_bidstack();
        },

        is_filtered(param, value){
            if(this.selected_filters[param]==null){
                return false;
            }
            for(var i = 0; i< this.selected_filters[param].length; i++){
                if(this.selected_filters[param][i] == value){
                    return true;
                }
            }
            return false;
        },

        add_filter(param, value){
            console.log('Adding filter', param, value)
            if(this.selected_filters[param]==null){
                this.selected_filters[param] = [];
            }
            this.selected_filters[param].push(value);
        },
        remove_filter(param, value){
            console.log('Removing filter', param, value)
            var remaining_filters = [];
            for(var i = 0; i< this.selected_filters[param].length; i++){
                if(this.selected_filters[param][i] != value){
                    remaining_filters.push(this.selected_filters[param][i]);
                }
            }
            this.selected_filters[param] = remaining_filters;
        },

        

        apply_filters(){
            console.log('Selected filters changed.');
            var new_sorted_bidstack = [];
            for(var i = 0; i< this.sorted_bidstack.length; i++){
                var bid = this.sorted_bidstack[i];
                
            }
            this.sorted_bidstack = new_sorted_bidstack;
        },

        reset_bidstack(){
            this.sorted_bidstack = [];
            this.total_volume = 0;
            this.max_price = 0;
            this.min_price = 0;
            this.colors = {}
        },

        

        get_height_percent(price){

            var max = Math.min(this.max_price, this.chart_price_cap);
            var min = Math.max(this.min_price, this.chart_price_floor);

            var price = Math.max(price, this.chart_price_floor);
            price = Math.min(price, this.chart_price_cap);
            
            percent = Math.abs(100.0 * price / (max - min))
            if(percent >=0 && percent < 1){
                return 1
            }else if(percent > -1 && percent < 1){
                return -1;
            }else{
                return percent;
            }
            
        },

        get_width_percent(volume){
            return 100.0 * volume / this.total_volume;
        },

        get_marginal_benefit_width_percent(volume){
            return 100.0 * volume / this.marginal_benefit_total_volume;
        },
        
        get_transform(price){

            if(price < 0){
                return "translateY(100%)"
            }else{
                return"none";
            }

        },


        get_color(bid){
            // var my_palette = ["ffb3ba", "ffdfba", "ffffba", "baffc9", "bae1ff"];
            // my_palette.push.apply(my_palette,palette('mpn65', 15) );

            

            // // var my_palette = palette('mpn65', 15);
            // index = Math.floor(Math.random() * my_palette.length);
            
            // if(!this.colors[bid.generator]){
            //     this.colors[bid.generator] = my_palette[index];
            // }
            // color = this.colors[bid.generator];
            var colorHashObj =  new ColorHash();
            
            var colorHash = colorHashObj.rgb(bid.meta.label);
            // console.log('Color hash test',colorHash)

            var color = ""
            for(var i = 0; i< colorHash.length; i++){
                color += colorHash[i].toString(16);
            }
            
            if(bid.meta.label == this.selected_bid.meta.label){
                color = "000000";
            }

            return "#"+color
        },

        date_to_str(date_iso){
            return moment.unix(date_iso).format('YYYY MMM DD HH:mm');
        },

        select_bidstack(date_iso){
            console.log('Selecting bidstack', date_iso);
            this.date_iso = date_iso;
            this.reset_bidstack();
            var self = this;
            if(this.saved_bidstacks[this.state][this.date_iso] == null){
                $.getJSON('/bidstack/'+this.state+'/'+date_iso, function(response){
                    console.log('bidstack', response);
                    
                    self.saved_bidstacks[self.state][self.date_iso] = response;
                    for(var key in response){
                        
                        for(var filter in self.filters){
                            var option = response[key].meta[filter];
                            //Check if its an empty string or nonsensical
                            if (!option.match(/[a-z]/i)) {
                                option="Other"
                                response[key].meta[filter] = option;
                            }

                            if(self.filters[filter].indexOf(option) < 0){
                                self.filters[filter].push(option)
                            }
                            
                        }
                    }

                    self.draw_bidstack();
                });
            }else{
                self.draw_bidstack();
            }
            

        },

        select_bid(bid){
            this.selected_bid = bid;
        },
        draw_bidstack(){
            this.reset_bidstack();

            //Assemble data
            var sorted_bidstack = [];
            var original_bidstack = this.saved_bidstacks[this.state][this.date_iso];
            for(var name in original_bidstack){
                var bid = original_bidstack[name];
                var data = [];
                //Check filters
                var include = true;
                for(var property_type in this.selected_filters){
                    
                    for(var j=0; j< this.selected_filters[property_type].length; j++){
                        var property = this.selected_filters[property_type][j];
                        if(bid.meta[property_type] == property){
                            include = false;
                        }
                    }
                    
                }
                //If it hasnt been filtered, add it to the sorted bidstack.
                if(include){

                    for(var band in original_bidstack[name].bands){
                        if(original_bidstack[name].bands[band].volume > 0){
                            
                            sorted_bidstack.push({
                                'generator':name,
                                'volume':original_bidstack[name].bands[band].volume,
                                'price':original_bidstack[name].bands[band].price,
                                'meta':original_bidstack[name].meta,
                            })
                            
                            this.total_volume += original_bidstack[name].bands[band].volume

                            if(original_bidstack[name].bands[band].price > this.max_price){
                                this.max_price = original_bidstack[name].bands[band].price;
                            }

                            if(original_bidstack[name].bands[band].price < this.min_price){
                                this.min_price = original_bidstack[name].bands[band].price;
                            }
                            
                        }
                    }
                }
                
            }
            //Sort the sorted bidstack.
            sorted_bidstack.sort(function(a, b){
                return a.price - b.price;
            });
            //set the variable globally. Bidstack will be drawn via html v-for.
            this.sorted_bidstack = sorted_bidstack;
        

        },

        drawSpot(){
            var self = this;
            $.getJSON('/spotprices/'+this.state+'/'+this.dates[0]+'/'+this.dates[this.dates.length-1], function(result){
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
                var series = [];
                for(var state in result){
                    console.log(state)
                    series.push(
                        {
                            type: 'line',
                            name: state+' Spot Price',
                            yaxis: 1,
                            data: result[state].spot.prices
                        },
                    )
                }
               

                  Highcharts.chart('spotprices', {
                    chart: {
                        zoomType: 'xy'
                    },
                    title: {
                        text: self.state+" Spot Prices"
                    },
                    // subtitle: {
                    //     text: document.ontouchstart === undefined ?
                    //             'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
                    // },
                    xAxis: {
                        type: 'datetime',
                    },
                    yAxis: [{
                        title: {
                            text: 'Price $/MWh'
                        }
                    },
                    // {
                    //     title: {
                    //         text: 'Demand MW'
                    //     },
                    //     opposite:true,
                    // }
                ],
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
                        series:{
                            cursor: 'pointer',
                            point: {
                                events: {
                                    click: function () {
                                        // alert('Category: ' + this.category + ', value: ' + this.y);
                                        self.select_bidstack(this.category/1000);
                                    }
                                }
                            }
                        },
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
        
                    series: series,
                });
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
            self.drawSpot();
        });
    }
})