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
participant_states = {p:participant_service.participant_metadata[p]['state'] for p in participant_service.participant_metadata}
relevant_duids = [duid for duid in participant_states]

for date in dates:
    print("LMP_VCG",date)
    demand = {}
    total_demand = 0
    # Get demand for each state.
    for state in states:
        demand[state] = Demand.objects(date_time=date, region=state).get().demand
        total_demand += demand[state]

    stack = BidStack.objects(trading_period=date).get()

    all_bids = []
    
    lookup_duids = {}
    lookup_participant_id = {}
    all_participant_ids = []

    # Assemble a sortable bidstack
    for duid in stack.getParticipants():
        if duid in relevant_duids:
            bid = stack.getBid(duid)
            # bidder_ids[duid] = bid.bid_day_offer.PARTICIPANTID
            participant_id = bid.bid_day_offer.PARTICIPANTID 
            if participant_id not in lookup_duids:
                lookup_duids[participant_id] = []
            lookup_duids[participant_id].append(duid)
            lookup_participant_id[duid] = participant_id
            if participant_id not in all_participant_ids:
                all_participant_ids.append(participant_id)
            bid_list = [b for b in bid_to_list(bid) if b['volume'] > 0]
            for b in bid_list:
                b['duid'] = duid 
                # b['price'] = max(b['price'], 0)
                b['state'] = participant_states[duid]
            all_bids.extend(bid_list)
    

    # Perform economic dispatch
    sorted_bids = sorted(all_bids, key=lambda k: k['price'])
    nationwide_key_result = economic_dispatch(sorted_bids, total_demand)
    
    # Calculate total industrial cost for each state.
    total_industrial_cost = {state:0 for state in states}
    for bid in nationwide_key_result['used_bids']:
        total_industrial_cost[bid['state']] += bid['volume'] * bid['price']

    nationwide_total_industrial_cost = sum([total_industrial_cost[state] for state in states]) 

    participant_payments = {state:{} for state in states}
    # Compare economic dispatch price to each economic dispatch price with each participant removed
    for participant_id in all_participant_ids: #participant_ids are the keys in the lookup_duids dict. confusing, i know.
        # Split bid stack into those from the participant, those not from the participant.
        redacted_bids = [bid for bid in sorted_bids if bid['duid'] not in lookup_duids[participant_id]]
        participant_bids = [bid for bid in sorted_bids if bid['duid'] in lookup_duids[participant_id]]
        # Perform economic dispatch without the participant. 
        result = economic_dispatch(redacted_bids, total_demand)

        # Calculate total industrial cost for each state
        participant_total_industrial_cost = {state:0 for state in states}
        for bid in result['used_bids']:
            participant_total_industrial_cost[bid['state']] += bid['volume'] * bid['price']
        
        # Save the relevant price and volume
        for state in states:
            participant_payments[state][participant_id] = sum([bid['volume'] * bid['price'] for bid in nationwide_key_result['used_bids'] if bid['state'] == state]) #sum of the bids
            participant_payments[state][participant_id] += (participant_total_industrial_cost[state] - total_industrial_cost[state]) #


    for state in states:
        total_cost = 0
        for participant_id in all_participant_ids:
            if participant_id in participant_payments[state]:
                total_cost += participant_payments[state][participant_id]
        
        average_price = total_cost / demand[state]
        

        price = Price(
            date_time = date,
            price = average_price,
            region = state,
            price_type ='LMP_VCG',
        )
        price.save()


