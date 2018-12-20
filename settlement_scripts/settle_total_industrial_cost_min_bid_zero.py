from application.model.participants import ParticipantService
from application.model.demand import Demand
from application.model.price import Price
participant_service = ParticipantService()
import pendulum
from application import config


from application.model.bidstack import BidStack, DoesNotExist, bid_to_dict, bid_to_list



def economic_dispatch(sorted_bids, demand):
    used_bids = []
    current = sorted_bids[0]
    cumulative_supply = 0
    for bid in sorted_bids:
        current = bid
        prev_supply = cumulative_supply
        cumulative_supply += bid['volume']
        if cumulative_supply > demand:
            current['dispatched'] = demand - prev_supply
            used_bids.append(current)
            break
        current['dispatched'] = current['volume']
        used_bids.append(current)
    return {'price':current['price'], 'used_bids':used_bids}


dates = BidStack.objects().distinct('trading_period')
dates = [date for date in dates if (pendulum.instance(date).minute==0 or pendulum.instance(date).minute==30)]
states = ['NSW', 'QLD', 'VIC', 'QLD', 'TAS']

participants = {}
for state in states:
    participants[state] = [p for p in participant_service.participant_metadata if participant_service.participant_metadata[p]['state'] == state]

for state in states:
    for date in dates:
        
        if not Price.objects(date_time = date, region=state, price_type='TOTAL_INDUSTRIAL_COST_MIN_BID_ZERO'):
            print("TOTAL_INDUSTRIAL_COST_MIN_BID_ZERO", date)
            stack = BidStack.objects(trading_period=date).get()
            demand = Demand.objects(date_time=date, region=state).get().demand
            all_bids = []
           
            lookup_duids = {}
            lookup_participant_id = {}
            # Assemble a sortable bidstack
            for duid in stack.getParticipants():
                if duid in participants[state]:
                    bid = stack.getBid(duid)
                    # bidder_ids[duid] = bid.bid_day_offer.PARTICIPANTID
                    participant_id = bid.bid_day_offer.PARTICIPANTID 
                    if participant_id not in lookup_duids:
                        lookup_duids[participant_id] = []
                    lookup_duids[participant_id].append(duid)
                    lookup_participant_id[duid] = participant_id
                    bid_list = [b for b in bid_to_list(bid) if b['volume'] > 0]
                    for b in bid_list:
                        b['duid'] = duid 
                        b['price'] = max(b['price'], 0)
                    all_bids.extend(bid_list)
            
            # Perform economic dispatch
            sorted_bids = sorted(all_bids, key=lambda k: k['price'])
            key_result = economic_dispatch(sorted_bids, demand)
            total_industrial_cost = sum([bid['volume'] * bid['price'] for bid in key_result['used_bids']])

            
            price = Price(
                date_time = date,
                price = total_industrial_cost / demand,
                region = state,
                price_type ='TOTAL_INDUSTRIAL_COST_MIN_BID_ZERO',
            )
            price.save()