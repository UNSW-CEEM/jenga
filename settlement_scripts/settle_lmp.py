from application.model.participants import ParticipantService
from application.model.demand import Demand
from application.model.price import Price
participant_service = ParticipantService()
import pendulum
from application import config


from application.model.bidstack import BidStack, DoesNotExist, bid_to_dict, bid_to_list

dates = BidStack.objects().distinct('trading_period')
dates = [date for date in dates if (pendulum.instance(date).minute==0 or pendulum.instance(date).minute==30)]
states = ['NSW', 'QLD', 'VIC', 'QLD', 'TAS', 'SA']
participant_states = {}
participants = {}
for state in states:
    participants[state] = [p for p in participant_service.participant_metadata if participant_service.participant_metadata[p]['state'] == state]
participant_states = {p:participant_service.participant_metadata[p]['state'] for p in participant_service.participant_metadata}


for date in dates:
    print("LMP", date)
    demand = {}
    total_demand = 0
    # Get demand for each state.
    for state in states:
        demand[state] = Demand.objects(date_time=date, region=state).get().demand
        total_demand += demand[state]

    # Perform system-wide economic dispatch
    relevant_bids = [] # Will hold all bids > 0 volume
    stack = BidStack.objects(trading_period=date).get() # Get the bid stack
    for duid in stack.getParticipants():
        bid = stack.getBid(duid)
        bid_list = [b for b in bid_to_list(bid) if b['volume'] > 0]
        for b in bid_list:
            b['duid'] = duid 
        relevant_bids.extend(bid_list)

    # Perform economic dispatch
    sorted_bids = sorted(relevant_bids, key=lambda k: k['price'])
    used_bids = []
    current = sorted_bids[0]
    cumulative_supply = 0
    for bid in sorted_bids:
        if bid['duid'] in participant_states: #if the participant is a registered generator, and thus has metadata
            current = bid
            cumulative_supply += bid['volume']
            used_bids.append(bid)
            if cumulative_supply > total_demand:
                break
    
    
    # Determine marginal price in each region
    prices = {state:0 for state in states}
    for bid in used_bids:
        
        # Find which state the participant is in
        
        state = participant_states[bid['duid']]
        # Adjust the price in each state to find the maximum bid.
        if bid['price'] > prices[state] and bid['duid'] in participants[state]:
            prices[state] = bid['price']
        # prices[state] = bid['price'] if bid['price'] > prices[state] and bid['duid'] in participants[state] else prices[state]
    print(prices)
    for state in prices:
        
        price = Price(
                date_time = date,
                price = prices[state],
                region = state,
                price_type ='LMP',
            )
        price.save()

