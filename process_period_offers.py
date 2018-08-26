# This script splits up AEMO bid files and reads them into a MongoDB database.

import csv
from itertools import islice
from bid_model import BidDayOffer, BidPerOffer
import pendulum
import json
import hashlib

path = "data/PUBLIC_DVD_BIDPEROFFER_D_201806010000.CSV"

# AEMO's CSV files are actually two csv files in one! lucky us. 
# We need to find where the split is so we can use different headings etc.


print("Processing Bid Period Offers")
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
			if not BidPerOffer.objects(rowhash = rowhash):
				print("Saving Bid Period Offer ",rowhash)
				bid = BidPerOffer(
					SETTLEMENTDATE = row['SETTLEMENTDATE'],
					DUID = row['DUID'],
					BIDTYPE = row['BIDTYPE'],
					BIDSETTLEMENTDATE = row['BIDSETTLEMENTDATE'],
					OFFERDATE = row['OFFERDATE'],
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
					LASTCHANGED = row['LASTCHANGED'],
					PASAAVAILABILITY = row['PASAAVAILABILITY'],
					INTERVAL_DATETIME = row['INTERVAL_DATETIME'],
					MR_CAPACITY = row['MR_CAPACITY'],
					rowhash = rowhash
				)
				bid.save()
			