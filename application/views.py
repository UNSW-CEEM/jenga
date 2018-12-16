from application import app
from flask import render_template, jsonify
from application.model.bid_model import BidDayOffer
from application.model.bidstack import BidStack, DoesNotExist, bid_to_dict
import pendulum
import config
from application.model.price import Price
from application.model.demand import Demand
from application.model.participants import ParticipantService
participant_service = ParticipantService()


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

@app.route('/bidstack/<state>/<isodate>')
def bid_stack(state, isodate):
    state = state.upper()
    participant_meta = participant_service.participant_metadata
    if state != "ALL":
        participants_in_state = [p for p in participant_meta if participant_meta[p]['state'] == state ]
    else:
        participants_in_state = [p for p in participant_meta]

    date = pendulum.from_timestamp(int(isodate))
    try :
        stack = BidStack.objects(trading_period = date).get()
        bids = {}
        for name in stack.getParticipants():
            if name in participants_in_state:
                bid = stack.getBid(name)
                bids[name] = bid_to_dict(bid)

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

    demand_search = Demand.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper()).order_by('date_time')
    demand_result = [p for p in demand_search]

    basic_dispatch_price = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='BASIC').order_by('date_time')
    basic_dispatch_result = [p for p in basic_dispatch_price]
    
    basic_min_bid_zero_price = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='BASIC_MIN_BID_ZERO').order_by('date_time')
    basic_min_bid_zero_result = [p for p in basic_min_bid_zero_price]

    lmp_dispatch_price = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='LMP').order_by('date_time')
    lmp_dispatch_result = [p for p in lmp_dispatch_price]
    

    basic_vcg_price = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='BASIC_VCG').order_by('date_time')
    basic_vcg_result = [p for p in basic_vcg_price]

    basic_vcg_min_bid_zero_price = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='BASIC_VCG_MIN_BID_ZERO').order_by('date_time')
    basic_vcg_min_bid_zero_result = [p for p in basic_vcg_min_bid_zero_price]

    lmp_vcg_price = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='LMP_VCG').order_by('date_time')
    lmp_vcg_result = [p for p in lmp_vcg_price]

    lmp_vcg_min_bid_zero_price = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='LMP_VCG_MIN_BID_ZERO').order_by('date_time')
    lmp_vcg_min_bid_zero_result = [p for p in lmp_vcg_min_bid_zero_price]

    total_industrial_cost_price = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='TOTAL_INDUSTRIAL_COST').order_by('date_time')
    total_industrial_cost_result = [p for p in total_industrial_cost_price]

    total_industrial_cost_min_bid_zero_price = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='TOTAL_INDUSTRIAL_COST_MIN_BID_ZERO').order_by('date_time')
    total_industrial_cost_min_bid_zero_result = [p for p in total_industrial_cost_min_bid_zero_price]
    
    return jsonify({
                'spot':{
                    # 'dates':[ p.date_time for p in result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, p.price] for p in result]
                },
                'demand':{
                    # 'dates':[ p.date_time for p in demand_result],
                    'demand':[ [pendulum.instance(p.date_time).timestamp() * 1000, p.demand] for p in demand_result]
                },
                'basic_dispatch':{
                    # 'dates':[ p.date_time for p in basic_dispatch_result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, p.price] for p in basic_dispatch_result]
                },
                'basic_min_bid_zero':{
                    # 'dates':[ p.date_time for p in basic_min_bid_zero_result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, p.price] for p in basic_min_bid_zero_result]
                },
                'lmp_dispatch':{
                    # 'dates':[ p.date_time for p in lmp_dispatch_result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, p.price] for p in lmp_dispatch_result]
                },
                'basic_vcg_dispatch':{
                    # 'dates':[ p.date_time for p in basic_vcg_result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, round(p.price, 2)] for p in basic_vcg_result]
                },
                'basic_vcg_min_bid_zero_dispatch':{
                    # 'dates':[ p.date_time for p in basic_vcg_min_bid_zero_result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, round(p.price, 2)] for p in basic_vcg_min_bid_zero_result]
                },
                'lmp_vcg_dispatch':{
                    # 'dates':[ p.date_time for p in lmp_vcg_result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, round(p.price, 2)] for p in lmp_vcg_result]
                },
                'lmp_vcg_min_bid_zero_dispatch':{
                    # 'dates':[ p.date_time for p in lmp_vcg_min_bid_zero_result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, round(p.price, 2)] for p in lmp_vcg_min_bid_zero_result]
                },
                'total_industrial_cost':{
                    # 'dates':[ p.date_time for p in lmp_vcg_result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, round(p.price, 2)] for p in total_industrial_cost_result]
                },
                'total_industrial_cost_min_bid_zero':{
                    # 'dates':[ p.date_time for p in lmp_vcg_result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, round(p.price, 2)] for p in total_industrial_cost_min_bid_zero_result]
                },
            }
        )


@app.route('/spotprices/<region>/<start_isodate>/<end_isodate>')
def spotprices(region, start_isodate, end_isodate):
    start_date = pendulum.from_timestamp(int(start_isodate), tz=config.TZ)
    end_date = pendulum.from_timestamp(int(end_isodate), tz=config.TZ)
    print(start_date, end_date)
   
    search = Price.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper(), price_type='AEMO_SPOT').order_by('date_time')
    result = [p for p in search]

    demand_search = Demand.objects(date_time__gte=start_date, date_time__lte=end_date, region=region.upper()).order_by('date_time')
    demand_result = [p for p in demand_search]

    
    return jsonify({
                'spot':{
                    # 'dates':[ p.date_time for p in result],
                    'prices':[ [pendulum.instance(p.date_time).timestamp() * 1000, p.price] for p in result]
                },
                'demand':{
                    # 'dates':[ p.date_time for p in demand_result],
                    'demand':[ [pendulum.instance(p.date_time).timestamp() * 1000, p.demand] for p in demand_result]
                },
            }
        )