from application.model.bidstack import BidStack
from application.model.bid_model import BidPerOffer
import mongoengine

# Get all the dates
dates = BidPerOffer.objects().distinct('INTERVAL_DATETIME')
counter = 0
for date in dates:
    if counter > 131:
        print(date)
        try:
            if BidStack.objects(trading_period=date).count() == 0:
                s = BidStack(date)
                s.save()
            else:
                print ("Already exists")
        except mongoengine.errors.NotUniqueError:
            print("Bidstack already exists for ", date)
    counter += 1

