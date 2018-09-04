import os
import csv
import pendulum
import config
from application.model.demand import Demand
from application.model.price import Price

from string import digits
remove_digits = str.maketrans('', '', digits)

path = os.path.join('data', 'nem_spot')

for filename in os.listdir(path):
    print(filename)
    if 'csv' in filename:
        with  open(os.path.join(path, filename)) as f:
            reader = csv.DictReader(f)
            for line in reader:
                demand = Demand(
                    date_time=pendulum.parse(line['SETTLEMENTDATE'], tz=config.TZ), 
                    demand=line['TOTALDEMAND'], 
                    region=line['REGION'].translate(remove_digits)
                )
                demand.save()
                price = Price(
                    date_time = pendulum.parse(line['SETTLEMENTDATE'], tz=config.TZ),
                    price = line['RRP'],
                    region = line['REGION'].translate(remove_digits),
                    price_type ='AEMO_SPOT'
                )
                price.save()