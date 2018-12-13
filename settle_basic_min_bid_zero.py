from application.model.participants import ParticipantService
from application.model.demand import Demand
from application.model.price import Price
participant_service = ParticipantService()
import pendulum
from application import config


from application.model.bidstack import BidStack, DoesNotExist, bid_to_dict, bid_to_list

dates = BidStack.objects().distinct('trading_period')
dates = [date for date in dates if (pendulum.instance(date).minute==0 or pendulum.instance(date).minute==30)]
states = ['NSW', 'QLD', 'VIC', 'QLD', 'TAS']

participants = {}
for state in states:
    participants[state] = [p for p in participant_service.participant_metadata if participant_service.participant_metadata[p]['state'] == state]

for state in states:
    for date in dates:
        if not Price.objects(date_time = date, region=state, price_type='BASIC_MIN_BID_ZERO'):
            print('Adding', state, date)
            # Basic settlement.
            rounded_time = pendulum.instance(date, tz=config.TZ)
            if rounded_time.minute > 30:
                rounded_time = rounded_time.start_of('hour').add(hours=1)
            else:
                rounded_time = rounded_time.start_of('hour').add(minutes=30)
            print('rounded time', rounded_time)
            demand = Demand.objects(date_time=rounded_time, region=state).get().demand
            print('demand', demand)
            
            stack = BidStack.objects(trading_period=date).get()
            
            all_bids = []
            # Assemble a sortable bidstack
            for name in stack.getParticipants():
                if name in participants[state]:
                    bid = stack.getBid(name)
                    
                    bid_list = [b for b in bid_to_list(bid) if b['volume'] > 0]
                    for bid in bid_list:
                        bid['price'] = max(bid['price'], 0)
                    all_bids.extend(bid_list)
            
            # Perform economic dispatch
            sorted_bids = sorted(all_bids, key=lambda k: k['price'])
            used_bids = []
            current = sorted_bids[0]
            cumulative_supply = 0
            for idx, bid in enumerate(sorted_bids):
                current = bid
                cumulative_supply += bid['volume']
                used_bids.append(bid)
                if cumulative_supply > demand:
                    break

            
            price = Price(
                date_time = date,
                price = current['price'],
                region = state,
                price_type ='BASIC_MIN_BID_ZERO',
            )
            price.save()