import os
import csv
import pendulum
import config
from application.model.demand import Demand
from application.model.price import Price

from string import digits
import requests

def parse_all():
    remove_digits = str.maketrans('', '', digits)

    path = os.path.join('data', 'nem_spot_update')

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

def download():
    regions = ['QLD', 'NSW', 'VIC', 'SA', 'TAS']
    years = [1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019]
    # years = [2012]
    months = ["01","02","03","04","05","06","07","08","09","10","11","12"]
    for year in years:
        for month in months:
            for region in regions:
                print(year, month, region)
                fname = "PRICE_AND_DEMAND_"+str(year)+month+"_"+region+"1.csv"
                url = "https://www.aemo.com.au/aemo/data/nem/priceanddemand/"+fname
                
                r = requests.get(url)
                # print(r.content)
                if r.status_code == 200:
                    with open(os.path.join('data', 'nem_spot', fname), 'wb') as f:
                        f.write(r.content)
                else:
                    print("Could not download", url)

if __name__== "__main__":
    download()
    parse_all()