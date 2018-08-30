console.log('Gday mate');

Vue.component('price-chart',{
    template:`
        <div class="price-chart">
            <h1>Price Chart</h1>
            <div class="ct-chart "></div>
        </div>
    `,
    mounted(){
        var data = {
            // A labels array that can contain any sort of values
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            // Our series array that contains series objects or in this case series data arrays
            series: [
              [5, 2, 4, 2, 0]
            ]
          };
          
          // Create a new line chart object where as first parameter we pass in a selector
          // that is resolving to our chart container element. The Second parameter
          // is the actual data object.
          new Chartist.Line('.ct-chart', data);
    }
})

Vue.component('stack-explorer',{
    template:`
        <h1>Stack Explorer</h1>
    `
})


var app = new Vue({
    el:'.content',
    delimiters:['[[',']]'],
    data:{
        hello:'HI THERE'
    },
});