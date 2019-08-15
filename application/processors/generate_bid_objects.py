from application.model.bidstack import BidStack
from application.model.bid_model import BidPerOffer
import mongoengine
import pendulum

# Get all the dates
# dates = BidPerOffer.objects().distinct('INTERVAL_DATETIME')
# dates = sorted(dates)

if __name__ == "__main__":
    counter = 0

    start_date = pendulum.datetime(2018,11,28,12, tz="Australia/Brisbane")
    end_date = pendulum.datetime(2018,12,29,12, tz="Australia/Brisbane")
    date = start_date
    # for date in dates:
    while date < end_date:
        # if counter > 131:
        print(date)
        try:
            if BidStack.objects(trading_period=date).count() == 0:
                s = BidStack(date)
                s.save()
            else:
                print ("Already exists")
        except mongoengine.errors.NotUniqueError:
            print("Bidstack already exists for ", date)
        # counter += 1
        date = date.add(minutes=30)

