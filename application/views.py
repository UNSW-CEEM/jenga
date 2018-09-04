from application import app
from flask import render_template, jsonify
from application.model.bid_model import BidDayOffer
from application.model.bidstack import BidStack, DoesNotExist, bid_to_dict
import pendulum
import config
from application.model.price import Price
@app.route('/')
def main():
    return render_template('index.html')

@app.route('/offers/<isodate>')
def available_dates(isodate):
    date = pendulum.from_timestamp(int(isodate), tz=config.TZ)
    result = BidDayOffer.objects(SETTLEMENTDATE=date.start_of('day'))
    return jsonify([x.to_dict() for x in result])

@app.route('/bids/<isodate>')
def bids(isodate):
    date = pendulum.from_timestamp(int(isodate), tz=config.TZ)

@app.route('/bidstack/<isodate>')
def bid_stack(isodate):
    date = pendulum.from_timestamp(int(isodate))
    try :
        stack = BidStack.objects(trading_period = date).get()
        
        bids = {}
        
        for name in stack.getParticipants():
            bid = stack.getBid(name)
            # bid_dict = bid_to_dict(bid)
            bids[name] = bid_to_dict(bid)
            # for i in range(1,10):
            #     # Only keep it if there was an actual volume bid.
            #     # if bid_dict[i]['volume']:
            #     bids[name] = bid_to_dict(bid)
            #     break

        print(date, stack)
        
        return jsonify(bids)
    except DoesNotExist:
        print("Couldn't find stack")
    
        return jsonify({'message':'None found.'})

@app.route('/bidstack/dates')
def bid_stack_dates():
    dates = BidStack.objects().distinct('trading_period')
    return jsonify([pendulum.instance(date).timestamp() for date in dates])
    

@app.route('/prices/<region>/<start_isodate>/<end_isodate>')
def prices(region, start_isodate, end_isodate):
    start_date = pendulum.from_timestamp(int(start_isodate), tz=config.TZ)
    end_date = pendulum.from_timestamp(int(end_isodate), tz=config.TZ)
    print(start_date, end_date)
    search = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='AEMO_SPOT').order_by('date_time')
    result = [p for p in search]
    
    return jsonify({
                'spot':{
                    'dates':[ p.date_time for p in result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, p.price] for p in result]
                    
                }
            }
        )
