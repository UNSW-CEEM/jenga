# This script splits up AEMO bid files and reads them into a MongoDB database.

import csv
from itertools import islice
from application.bid_model import BidDayOffer, BidPerOffer
import pendulum
import json
import hashlib
import config
from mongoengine.errors import NotUniqueError

path = "data/PUBLIC_DVD_BIDDAYOFFER_D_201806010000.CSV"

# AEMO's CSV files are actually two csv files in one! lucky us. 
# We need to find where the split is so we can use different headings etc.
def run(path):
    print("Processing Bid Day Offers")
    # Process the first set of data - the daily offers.
    # Daily offers are where the bidder sets the prices of their price bands and a few other predicted params
    with open(path, 'rt') as f:
        # Skip first row
        
        # Read the values from the csv file into a python dictionary object. 
        reader = csv.DictReader(islice(f, 1, None), delimiter=',')
        # Loop through every row of data.
        for row in reader:
            
            if row['BIDTYPE'] == 'ENERGY':
                print (row)
                # grab a hash of the line dict.
                rowhash = str(hashlib.sha256(json.dumps(dict(row), sort_keys=True).encode('utf-8')).hexdigest())
                # Make empty strings into None objects.
                for key in row:
                    row[key] = None if row[key] == "" else row[key]
                # If the bid isn't currently in the dataset
                try:
                    print ("Saving Bid Day Offer ", rowhash)
                    # Create the object
                    offer = BidDayOffer(
                        SETTLEMENTDATE = pendulum.parse(row['SETTLEMENTDATE'], tz=config.TZ),
                        DUID = row['DUID'],
                        BIDTYPE = row['BIDTYPE'],
                        BIDSETTLEMENTDATE = pendulum.parse(row['BIDSETTLEMENTDATE'], tz=config.TZ),
                        OFFERDATE = pendulum.parse(row['OFFERDATE'], tz=config.TZ),
                        VERSIONNO = row['VERSIONNO'],
                        PARTICIPANTID = row['PARTICIPANTID'],
                        DAILYENERGYCONSTRAINT = row['DAILYENERGYCONSTRAINT'],
                        REBIDEXPLANATION = row['REBIDEXPLANATION'],
                        PRICEBAND1 = row['PRICEBAND1'],
                        PRICEBAND2 = row['PRICEBAND2'],
                        PRICEBAND3 = row['PRICEBAND3'],
                        PRICEBAND4 = row['PRICEBAND4'],
                        PRICEBAND5 = row['PRICEBAND5'],
                        PRICEBAND6 = row['PRICEBAND6'],
                        PRICEBAND7 = row['PRICEBAND7'],
                        PRICEBAND8 = row['PRICEBAND8'],
                        PRICEBAND9 = row['PRICEBAND9'],
                        PRICEBAND10 = row['PRICEBAND10'],
                        MINIMUMLOAD = row['MINIMUMLOAD'],
                        T1 = row['T1'],
                        T2 = row['T2'],
                        T3 = row['T3'],
                        T4 = row['T4'],
                        NORMALSTATUS = row['NORMALSTATUS'],
                        LASTCHANGED = pendulum.parse(row['LASTCHANGED'], tz=config.TZ),
                        MR_FACTOR = row['MR_FACTOR'],
                        ENTRYTYPE = row['ENTRYTYPE'],
                        rowhash = rowhash
                    )
                    # Save it to the db
                    offer.save()
                except NotUniqueError:
                    print("Didn't save - already in DB!")
                    pass


if __name__ == "__main__":
    run(path)