
Vue.component('bidstack',{
    template:`
        <div class="bidstack">
            BIDSTACK
            <select v-model="state">
                    <option disabled value="">Please select one</option>
                    <option>QLD</option>
                    <option>NSW</option>
                    <option>VIC</option>
                    <option>SA</option>
                    <option>TAS</option>
                </select>
            <div class="columns">
                <div class="column" v-for="(bid, index) in sorted_bidstack" v-on:click="select_bid(bid)" v-bind:style="{ height: get_height_percent(bid.price) + '%', width: get_width_percent(bid.volume) + '%', 'background-color':get_color(bid), transform:get_transform(bid.price)}">
                </div>
            </div>

            <div class="stats-row">
                <div class="bid-stats">
                    <h3>{{selected_bid.generator}}</h3
                    <span>
                        Bid Price: $ {{selected_bid.price}} / MWh
                    </span>
                    
                    <span>
                        Bid Volume: {{selected_bid.volume}} MWh
                    </span>
                   
                </div>

                <div class="marginal-benefit">
                
                    <div class="column" v-for="(bid, index) in selected_bid_marginal_benefit_curve" v-on:click="select_bid(bid)" v-bind:style="{ height: get_height_percent(bid.price) + '%', width: get_marginal_benefit_width_percent(bid.volume) + '%', transform:get_transform(bid.price)}">
                    </div>
                </div>

            </div>
            
        </div>
    `,
    data(){
        return{
            dates:[],
            bidstack : [],
            mode:'generator',
            state:'NSW',
            date_iso:0,
            total_volume:100,
            min_price:0,
            max_price:0,
            chart_price_cap:14000,
            chart_price_floor:-10000,
            selected_bid:{},
            
            sorted_bidstack:[],
            colors:{}
        }
    },
    watch:{
        state(){
            console.log('state changed to ', this.state);
            this.select_bidstack(this.date_iso)
        }
    },
    computed:{
        selected_bid_marginal_benefit_curve(){
            var selected_bid_marginal_benefit_curve = [];
            for(var i = 0; i< this.sorted_bidstack.length; i++){
                if(this.sorted_bidstack[i].generator == this.selected_bid.generator){
                    selected_bid_marginal_benefit_curve.push(this.sorted_bidstack[i]);
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

        reset_bidstack(){
            this.sorted_bidstack = 0;
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
            var my_palette = ["ffb3ba", "ffdfba", "ffffba", "baffc9", "bae1ff"];
            my_palette.push.apply(my_palette,palette('mpn65', 15) );

            

            // var my_palette = palette('mpn65', 15);
            index = Math.floor(Math.random() * my_palette.length);
            
            if(!this.colors[bid.generator]){
                this.colors[bid.generator] = my_palette[index];
            }
            color = this.colors[bid.generator];

            if(bid.generator == this.selected_bid.generator){
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
            $.getJSON('/bidstack/'+this.state+'/'+date_iso, function(response){
                console.log('bidstack', response);
                self.bidstack = response;
                self.draw_chart();
            });

        },

        select_bid(bid){
            this.selected_bid = bid;
        },
        draw_chart(){

            
            //Assemble data
            var sorted_bidstack = [];

            for(var name in this.bidstack){
                var data = [];
                for(var band in this.bidstack[name].bands){
                    if(this.bidstack[name].bands[band].volume > 0){
                        
                        sorted_bidstack.push({
                            'generator':name,
                            'volume':this.bidstack[name].bands[band].volume,
                            'price':this.bidstack[name].bands[band].price,
                        })
                        
                        this.total_volume += this.bidstack[name].bands[band].volume

                        if(this.bidstack[name].bands[band].price > this.max_price){
                            this.max_price = this.bidstack[name].bands[band].price;
                        }

                        if(this.bidstack[name].bands[band].price < this.min_price){
                            this.min_price = this.bidstack[name].bands[band].price;
                        }
                        
                    }
                }
                
            }

            sorted_bidstack.sort(function(a, b){
                return a.price - b.price;
            });

            this.sorted_bidstack = sorted_bidstack;


            

           
        

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