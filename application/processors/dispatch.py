# This script splits up AEMO bid files and reads them into a MongoDB database.

import csv
from itertools import islice
from application.model.dispatch import DispatchLoad
import pendulum
import json
import hashlib
import config
from mongoengine.errors import NotUniqueError



# AEMO's CSV files are actually two csv files in one! lucky us. 
# We need to find where the split is so we can use different headings etc.
BATCH_SIZE = 100000

def process(path, batch_mode = True):
    print("Processing Dispatch", path)
    # Process the first set of data - the daily offers.
    # Daily offers are where the bidder sets the prices of their price bands and a few other predicted params
    line_no = 0
    batch = []
    with open(path, 'rt') as f:
        # Skip first row
        # f.readline()
        # Read the values from the csv file into a python dictionary object. 
        reader = csv.DictReader(islice(f, 1, None), delimiter=',')
        # Loop through every row of data.     
        for row in reader:
            line_no += 1
            
            # grab a hash of the line dict.
            rowhash = str(hashlib.sha256(json.dumps(dict(row), sort_keys=True).encode('utf-8')).hexdigest())
            # Make empty strings into None objects.
            for key in row:
                row[key] = None if row[key] == "" else row[key]
            # If the bid isn't currently in the dataset
            dispatch = DispatchLoad(
                    SETTLEMENTDATE = pendulum.parse(row['SETTLEMENTDATE'], tz=config.TZ),
                    RUNNO = float(row['RUNNO']) if row['RUNNO'] else None,
                    DUID = row['DUID'],
                    TRADETYPE = row['TRADETYPE'],
                    DISPATCHINTERVAL = row['DISPATCHINTERVAL'],
                    INTERVENTION = row['INTERVENTION'],
                    CONNECTIONPOINTID = row['CONNECTIONPOINTID'],
                    DISPATCHMODE = row['DISPATCHMODE'],
                    AGCSTATUS = row['AGCSTATUS'],
                    INITIALMW = float(row['INITIALMW']) if row['INITIALMW'] else None,
                    TOTALCLEARED = float(row['TOTALCLEARED']) if row['TOTALCLEARED'] else None,
                    RAMPDOWNRATE = float(row['RAMPDOWNRATE']) if row['RAMPDOWNRATE'] else None,
                    RAMPUPRATE = float(row['RAMPUPRATE']) if row['RAMPUPRATE'] else None,
                    LOWER5MIN = float(row['LOWER5MIN']) if row['LOWER5MIN'] else None,
                    LOWER60SEC = float(row['LOWER60SEC']) if row['LOWER60SEC'] else None,
                    LOWER6SEC = float(row['LOWER6SEC']) if row['LOWER6SEC'] else None,
                    RAISE5MIN = float(row['RAISE5MIN']) if row['RAISE5MIN'] else None,
                    RAISE60SEC = float(row['RAISE60SEC']) if row['RAISE60SEC'] else None,
                    RAISE6SEC = float(row['RAISE6SEC']) if row['RAISE6SEC'] else None,
                    DOWNEPF = float(row['DOWNEPF']) if row['DOWNEPF'] else None,
                    UPEPF = float(row['UPEPF']) if row['UPEPF'] else None,
                    MARGINAL5MINVALUE = float(row['MARGINAL5MINVALUE']) if row['MARGINAL5MINVALUE'] else None,
                    MARGINAL60SECVALUE = float(row['MARGINAL60SECVALUE']) if row['MARGINAL60SECVALUE'] else None,
                    MARGINAL6SECVALUE = float(row['MARGINAL6SECVALUE']) if row['MARGINAL6SECVALUE'] else None,
                    MARGINALVALUE = float(row['MARGINALVALUE']) if row['MARGINALVALUE'] else None,
                    VIOLATION5MINDEGREE = float(row['VIOLATION5MINDEGREE']) if row['VIOLATION5MINDEGREE'] else None,
                    VIOLATION60SECDEGREE = float(row['VIOLATION60SECDEGREE']) if row['VIOLATION60SECDEGREE'] else None,
                    VIOLATION6SECDEGREE = float(row['VIOLATION6SECDEGREE']) if row['VIOLATION6SECDEGREE'] else None,
                    VIOLATIONDEGREE = float(row['VIOLATIONDEGREE']) if row['VIOLATIONDEGREE'] else None,
                    LASTCHANGED = pendulum.parse(row['LASTCHANGED'], tz=config.TZ), # Last date and time record changed 	DATE
                    LOWERREG = float(row['LOWERREG']) if row['LOWERREG'] else None,
                    RAISEREG = float(row['RAISEREG']) if row['RAISEREG'] else None,
                    AVAILABILITY = float(row['AVAILABILITY']) if row['AVAILABILITY'] else None,
                    RAISE6SECFLAGS = row['RAISE6SECFLAGS'],
                    RAISE60SECFLAGS = row['RAISE60SECFLAGS'],
                    RAISE5MINFLAGS = row['RAISE5MINFLAGS'],
                    RAISEREGFLAGS = row['RAISEREGFLAGS'],
                    LOWER6SECFLAGS = row['LOWER6SECFLAGS'],
                    LOWER60SECFLAGS = row['LOWER60SECFLAGS'],
                    LOWER5MINFLAGS = row['LOWER5MINFLAGS'],
                    LOWERREGFLAGS = row['LOWERREGFLAGS'],
                    RAISEREGAVAILABILITY = float(row['RAISEREGAVAILABILITY']) if row['RAISEREGAVAILABILITY'] else None,
                    RAISEREGENABLEMENTMAX = float(row['RAISEREGENABLEMENTMAX']) if row['RAISEREGENABLEMENTMAX'] else None,
                    RAISEREGENABLEMENTMIN = float(row['RAISEREGENABLEMENTMIN']) if row['RAISEREGENABLEMENTMIN'] else None,
                    LOWERREGAVAILABILITY = float(row['LOWERREGAVAILABILITY']) if row['LOWERREGAVAILABILITY'] else None,
                    LOWERREGENABLEMENTMAX = float(row['LOWERREGENABLEMENTMAX']) if row['LOWERREGENABLEMENTMAX'] else None,
                    LOWERREGENABLEMENTMIN = float(row['LOWERREGENABLEMENTMIN']) if row['LOWERREGENABLEMENTMIN'] else None,
                    RAISE6SECACTUALAVAILABILITY = float(row['RAISE6SECACTUALAVAILABILITY']) if row['RAISE6SECACTUALAVAILABILITY'] else None,
                    RAISE60SECACTUALAVAILABILITY = float(row['RAISE60SECACTUALAVAILABILITY']) if row['RAISE60SECACTUALAVAILABILITY'] else None,
                    RAISE5MINACTUALAVAILABILITY = float(row['RAISE5MINACTUALAVAILABILITY']) if row['RAISE5MINACTUALAVAILABILITY'] else None,
                    RAISEREGACTUALAVAILABILITY = float(row['RAISEREGACTUALAVAILABILITY']) if row['RAISEREGACTUALAVAILABILITY'] else None,
                    LOWER6SECACTUALAVAILABILITY = float(row['LOWER6SECACTUALAVAILABILITY']) if row['LOWER6SECACTUALAVAILABILITY'] else None,
                    LOWER60SECACTUALAVAILABILITY = float(row['LOWER60SECACTUALAVAILABILITY']) if row['LOWER60SECACTUALAVAILABILITY'] else None,
                    LOWER5MINACTUALAVAILABILITY = float(row['LOWER5MINACTUALAVAILABILITY']) if row['LOWER5MINACTUALAVAILABILITY'] else None,
                    LOWERREGACTUALAVAILABILITY = float(row['LOWERREGACTUALAVAILABILITY']) if row['LOWERREGACTUALAVAILABILITY'] else None,
                    rowhash = rowhash
                )

            print (line_no, " of 2,579,800 (approx) - Saving Bid Day Offer ", rowhash, path)
            
            batch.append(dispatch)
            if len(batch) >= BATCH_SIZE:
                print("Saving Batch")
                try:
                    DispatchLoad.objects.insert(batch)
                except NotUniqueError:
                    print("Item in batch already in DB - trying individually.")
                    for d in batch:
                        try:
                            d.save()
                        except NotUniqueError:
                            print("Didn't save - already in DB!", rowhash)
                batch = []
                        


if __name__ == "__main__":
    path = "data/DISPATCHLOAD/PUBLIC_DVD_DISPATCHLOAD_201801010000.CSV"
    process(path)