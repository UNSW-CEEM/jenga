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
states = ['NSW', 'QLD', 'VIC', 'QLD', 'TAS', 'SA']

participants = {}
for state in states:
    participants[state] = [p for p in participant_service.participant_metadata if participant_service.participant_metadata[p]['state'] == state]

for state in states:
    for date in dates:
        if not Price.objects(date_time = date, region=state, price_type='BASIC_VCG'):
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
                        # b['price'] = max(b['price'], 0)
                    all_bids.extend(bid_list)
            
            # Perform economic dispatch
            sorted_bids = sorted(all_bids, key=lambda k: k['price'])
            key_result = economic_dispatch(sorted_bids, demand)
            total_industrial_cost = sum([bid['volume'] * bid['price'] for bid in key_result['used_bids']])
            # participant_prices = {}
            # participant_volumes = {}
            participant_payments = {}
            # Compare economic dispatch price to each economic dispatch price with each participant removed
            for participant_id in lookup_duids: #participant_ids are the keys in the lookup_duids dict. confusing, i know.
                # Split bid stack into those from the participant, those not from the participant.
                redacted_bids = [bid for bid in sorted_bids if bid['duid'] not in lookup_duids[participant_id]]
                participant_bids = [bid for bid in sorted_bids if bid['duid'] in lookup_duids[participant_id]]
                # Perform economic dispatch without the participant. 
                result = economic_dispatch(redacted_bids, demand)
                participant_total_industrial_cost = sum([bid['volume'] * bid['price'] for bid in result['used_bids']])
                # Save the relevant price and volume
                # participant_prices[participant_id] = result['price'] #relevant price is the price without the participant. 
                # participant_volumes[participant_id] = sum([bid['volume'] for bid in key_result['used_bids']]) #relevant volume is the amount they are dispatched in the true case.
                participant_payments[participant_id] = sum([bid['volume'] * bid['price'] for bid in key_result['used_bids']]) #sum of the bids
                participant_payments[participant_id] += (participant_total_industrial_cost - total_industrial_cost) #plus their externality
            
            # Calculate the weighted average price, given that each participant is paid their externality.
            total_cost = sum([participant_payments[participant_id] for participant in lookup_duids])
            average_price = total_cost / demand
            

            price = Price(
                date_time = date,
                price = average_price,
                region = state,
                price_type ='BASIC_VCG',
            )
            price.save()

