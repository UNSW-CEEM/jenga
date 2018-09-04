from application.model.bid_model import BidDayOffer, BidPerOffer
# import pymongo
import config
import pendulum
from mongoengine import *

# db = pymongo.MongoClient(config.db_url, config.db_port)[config.db_name]


class Bid(EmbeddedDocument):
	"""A bid consists of multiple bands, with different volumes and prices."""
	# Store participant names and references to the original bid period offer and 
	
	bid_day_offer = ReferenceField(BidDayOffer)
	bid_period_offer = ReferenceField(BidPerOffer)
	participant = StringField()
	
	def get_price(self, band):
		prices = {
			1: self.bid_day_offer.PRICEBAND1,
			2: self.bid_day_offer.PRICEBAND2,
			3: self.bid_day_offer.PRICEBAND3,
			4: self.bid_day_offer.PRICEBAND4,
			5: self.bid_day_offer.PRICEBAND5,
			6: self.bid_day_offer.PRICEBAND6,
			7: self.bid_day_offer.PRICEBAND7,
			8: self.bid_day_offer.PRICEBAND8,
			9: self.bid_day_offer.PRICEBAND9,
		}
		return prices[band]
	
	def get_volume(self, band):
		
		volumes = {
			1: self.bid_period_offer.BANDAVAIL1,
			2: self.bid_period_offer.BANDAVAIL2,
			3: self.bid_period_offer.BANDAVAIL3,
			4: self.bid_period_offer.BANDAVAIL4,
			5: self.bid_period_offer.BANDAVAIL5,
			6: self.bid_period_offer.BANDAVAIL6,
			7: self.bid_period_offer.BANDAVAIL7,
			8: self.bid_period_offer.BANDAVAIL8,
			9: self.bid_period_offer.BANDAVAIL9,
		}
		return volumes[band]

		

class BidStack(Document):
	"""
	Bidstack object is a wrapper for the BidDayOffer and BidPeroffer classes.
	Unlike these objects, the BidStack object employs a custom data model that is not analogous to AEMO's models.
	It is designed to offer a clean and intuitive interface for exploring NEM bid stacks. 
	Each Bidstack object is expected to be specific to a given dispatch time period.
 	"""
	trading_period = DateTimeField(unique=True)
	bids = MapField(EmbeddedDocumentField(Bid))
	
	
	def clean(self):
		"""Pass the constructor a python datetime object and a BidStack object will be constructed with the relevant data filled."""
		
		# Convert the datetime object to a pendulum object.
		dt = pendulum.instance(self.trading_period, tz=config.TZ)
		
		# HOW COOL IS THE NEM trading periods sensibly start at 4:30 am not midnight!
		settlement_date = pendulum.instance(dt, tz=config.TZ)
		if(settlement_date.hour <= 4 and settlement_date.minute != 0):
			settlement_date = settlement_date.subtract(days=1)
		settlement_date = settlement_date.start_of('day')

		print("Settlement Date", settlement_date)
		
		# Find all relevant participant names
		# unique_names = db['bid_day_offer'].find({'BIDTYPE':'ENERGY'}).distinct('DUID')
		unique_names = BidDayOffer.objects(BIDTYPE='ENERGY', SETTLEMENTDATE=settlement_date).distinct('DUID')
		# unique_dates = BidDayOffer.objects(BIDTYPE='ENERGY').distinct('SETTLEMENTDATE')
		# [print(date) for date in unique_dates]

		# Loop through each bidder, get their day offer.
		self.bid_day_offers = {}
		self.bid_period_offers = {}
		

		search = BidDayOffer.objects(BIDTYPE='ENERGY', SETTLEMENTDATE=settlement_date).order_by('-OFFERDATE')
		for offer in search:
			if offer.DUID not in self.bid_day_offers:
				# print("Getting BidDayOffer", offer.DUID)
				self.bid_day_offers[offer.DUID] = offer
		
		
		# Loop through each bidder, get the set of volume bids.
		
		search = BidPerOffer.objects(BIDTYPE='ENERGY', INTERVAL_DATETIME=dt)
		for offer in search:
			print(offer.DUID)
			if offer.DUID in self.bid_day_offers:
				print("Getting BidPerOffer", offer.DUID)
				self.bid_period_offers[offer.DUID] = offer
			
			
		# Loop through each participant and add the bid object. 
		print("Creating bid objects NOW")
		for name in self.bid_period_offers:
			print('BID CREATION', name, self.bid_day_offers[name], self.bid_period_offers[name])
			# try:
			b = Bid( 
				bid_day_offer=self.bid_day_offers[name], 
				bid_period_offer= self.bid_period_offers[name], 
				participant=name)
			# b.save()
			self.bids[name] = b
				
			# except AttributeError:
				# print('BID CREATION FAILED', name, self.bid_day_offers[name], self.bid_period_offers[name])
				# b = None
				
				# self.bids[name].save()
		


	def getParticipants(self):
		"""Returns the list of participants who bid during this period."""
		return [name for name in self.bids]
	
	def getBid(self, name):
		"""Returns a bid object corresponding to a given participant"""
		return self.bids[name]

def bid_to_dict(bid):
	bands = {}
	for i in range(1,10):
		bands[i] = {'price':bid.get_price(i), 'volume':bid.get_volume(i)}
	return {'bands':bands}


if __name__ == "__main__":
	dt = pendulum.parse('2018-05-01 14:30:00.000', tz=None)
	print(dt)
	search = BidStack.objects(trading_period=dt)
	print(search)
	if len(search) > 0:
		bs = search[0]
	else:
		bs = BidStack(dt)
		bs.save()
		
	bid = bs.getBid('MINTARO')
	for i in range(1, 8):
		print (i, bid.get_price(i), bid.get_volume(i))