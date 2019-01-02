# This script splits up AEMO bid files and reads them into a MongoDB database.

import csv
from itertools import islice
from application.model.bid_model import BidDayOffer, BidPerOffer
import pendulum
import json
import hashlib
import config
from mongoengine.errors import NotUniqueError

path = "data/PUBLIC_DVD_BIDPEROFFER_D_201806010000.CSV"



print("Processing Bid Period Offers")

def process(path):
	# Process the second set of data - the period offers. 
	with open(path, 'rt') as f:
		reader = csv.DictReader(islice(f,1,None), delimiter=',')
		for row in reader:
			
			# If the bid isn't currently in the dataset
			if row['BIDTYPE'] == 'ENERGY':
				# grab a hash of the line dict.
				rowhash = str(hashlib.sha256(json.dumps(dict(row), sort_keys=True).encode('utf-8')).hexdigest())
				# Make empty strings into None objects.
				for key in row:
					row[key] = None if row[key] == "" else row[key]
				try:
					print("Saving Bid Period Offer ",rowhash)
					bid = BidPerOffer(
						SETTLEMENTDATE = pendulum.parse(row['SETTLEMENTDATE'], tz=config.TZ),
						DUID = row['DUID'],
						BIDTYPE = row['BIDTYPE'],
						BIDSETTLEMENTDATE = pendulum.parse(row['BIDSETTLEMENTDATE'], tz=config.TZ),
						OFFERDATE = pendulum.parse(row['OFFERDATE'], tz=config.TZ),
						PERIODID = row['PERIODID'],
						VERSIONNO = row['VERSIONNO'],
						MAXAVAIL = row['MAXAVAIL'],
						FIXEDLOAD = row['FIXEDLOAD'],
						ROCUP = row['ROCUP'],
						ROCDOWN = row['ROCDOWN'],
						ENABLEMENTMIN = row['ENABLEMENTMIN'],
						ENABLEMENTMAX = row['ENABLEMENTMAX'],
						LOWBREAKPOINT = row['LOWBREAKPOINT'],
						HIGHBREAKPOINT = row['HIGHBREAKPOINT'],
						BANDAVAIL1 = row['BANDAVAIL1'],
						BANDAVAIL2 = row['BANDAVAIL2'],
						BANDAVAIL3 = row['BANDAVAIL3'],
						BANDAVAIL4 = row['BANDAVAIL4'],
						BANDAVAIL5 = row['BANDAVAIL5'],
						BANDAVAIL6 = row['BANDAVAIL6'],
						BANDAVAIL7 = row['BANDAVAIL7'],
						BANDAVAIL8 = row['BANDAVAIL8'],
						BANDAVAIL9 = row['BANDAVAIL9'],
						BANDAVAIL10 = row['BANDAVAIL10'],
						LASTCHANGED = pendulum.parse(row['LASTCHANGED'], tz=config.TZ),
						PASAAVAILABILITY = row['PASAAVAILABILITY'],
						INTERVAL_DATETIME = pendulum.parse(row['INTERVAL_DATETIME'], tz=config.TZ),
						MR_CAPACITY = row['MR_CAPACITY'],
						rowhash = rowhash
					)
					bid.save()
				except NotUniqueError:
					print("Didn't save - already in DB!")
					pass

if __name__ == "__main__":
	process(path)