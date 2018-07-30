# This script splits up AEMO bid files and reads them into a MongoDB database.

import csv
from itertools import islice
from bid_model import BidDayOffer, BidPerOffer
import pendulum
import json
import hashlib

path = "data/PUBLIC_YESTBID_201805010000_20180502040545.CSV"

# AEMO's CSV files are actually two csv files in one! lucky us. 
# We need to find where the split is so we can use different headings etc.

# Find the line number where the data types split.
with open(path, 'rt') as f:
	idx = 0
	for line in f:
		if 'BIDPEROFFER' in line:
			print (line)
			data_break = idx
			break
		idx += 1

print ("Break in file found at ", data_break)
print("Processing Bid Day Offers")
# Process the first set of data - the daily offers.
# Daily offers are where the bidder sets the prices of their price bands and a few other predicted params
with open(path, 'rt') as f:
	# Read the values from the csv file into a python dictionary object. 
	reader = csv.DictReader(islice(f,1,data_break), delimiter=',')
	# Loop through every row of data.
	for row in reader:
		# grab a hash of the line dict.
		rowhash = str(hashlib.sha256(json.dumps(dict(row), sort_keys=True).encode('utf-8')).hexdigest())
		# Make empty strings into None objects.
		for key in row:
			row[key] = None if row[key] == "" else row[key]
		# If the bid isn't currently in the dataset
		if not BidDayOffer.objects(rowhash = rowhash):
			print ("Saving Bid Day Offer ", rowhash)
			# Create the object
			bid = BidDayOffer(
				SETTLEMENTDATE = row['SETTLEMENTDATE'], 
				DUID = row['DUID'], 
				BIDTYPE = row['BIDTYPE'], 
				BIDSETTLEMENTDATE = row['BIDSETTLEMENTDATE'], 
				BIDOFFERDATE = row['BIDOFFERDATE'], 
				FIRSTDISPATCH = row['FIRSTDISPATCH'], 
				FIRSTPREDISPATCH = row['FIRSTPREDISPATCH'], 
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
				LASTCHANGED = row['LASTCHANGED'], 
				BIDVERSIONNO = row['BIDVERSIONNO'], 
				MR_FACTOR = row['MR_FACTOR'], 
				ENTRYTYPE = row['ENTRYTYPE'], 
				rowhash = rowhash,
			)

			# Save it to the db
			bid.save()

print("Processing Bid Period Offers")
# Process the second set of data - the period offers. 
with open(path, 'rt') as f:
	reader = csv.DictReader(islice(f,data_break,None), delimiter=',')
	for row in reader:
		# grab a hash of the line dict.
		rowhash = str(hashlib.sha256(json.dumps(dict(row), sort_keys=True).encode('utf-8')).hexdigest())
		# Make empty strings into None objects.
		for key in row:
			row[key] = None if row[key] == "" else row[key]
		# If the bid isn't currently in the dataset
		if not BidPerOffer.objects(rowhash = rowhash):
			print("Saving Bid Period Offer ",rowhash)
			bid = BidPerOffer(
				SETTLEMENTDATE = row['SETTLEMENTDATE'],
				DUID = row['DUID'],
				BIDTYPE = row['BIDTYPE'],
				BIDSETTLEMENTDATE = row['BIDSETTLEMENTDATE'],
				BIDOFFERDATE = row['BIDOFFERDATE'],
				TRADINGPERIOD = row['TRADINGPERIOD'],
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
				PASAAVAILABILITY = row['PASAAVAILABILITY'],
				PERIODID = row['PERIODID'],
				LASTCHANGED = row['LASTCHANGED'],
				BIDVERSIONNO = row['BIDVERSIONNO'],
				MR_CAPACITY = row['MR_CAPACITY'],
				rowhash = rowhash,
			)
			bid.save()
			