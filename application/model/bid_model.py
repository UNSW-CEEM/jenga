from mongoengine import *
import config


connect(config.DB_NAME, host=config.MONGO_HOST,username=config.MONGO_USER, password=config.MONGO_PASSWORD, authentication_source=config.MONGO_AUTH_SOURCE)

class BidDayOffer(Document):
	SETTLEMENTDATE = DateTimeField()
	DUID = StringField()
	BIDTYPE = StringField()
	BIDSETTLEMENTDATE = DateTimeField()
	OFFERDATE = DateTimeField()
	VERSIONNO = IntField()
	PARTICIPANTID = StringField()
	DAILYENERGYCONSTRAINT = FloatField()
	REBIDEXPLANATION = StringField()
	PRICEBAND1 = FloatField()
	PRICEBAND2 = FloatField()
	PRICEBAND3 = FloatField()
	PRICEBAND4 = FloatField()
	PRICEBAND5 = FloatField()
	PRICEBAND6 = FloatField()
	PRICEBAND7 = FloatField()
	PRICEBAND8 = FloatField()
	PRICEBAND9 = FloatField()
	PRICEBAND10 = FloatField()
	MINIMUMLOAD = FloatField()
	T1 = FloatField()
	T2 = FloatField()
	T3 = FloatField()
	T4 = FloatField()
	NORMALSTATUS = StringField()
	LASTCHANGED = DateTimeField()
	MR_FACTOR = FloatField()
	ENTRYTYPE = StringField()
	rowhash = StringField(unique=True)

	def to_dict(self):
		return {
			'SETTLEMENTDATE' : self.SETTLEMENTDATE,
			'DUID' : self.DUID,
			'BIDTYPE' : self.BIDTYPE,
			'BIDSETTLEMENTDATE' : self.BIDSETTLEMENTDATE,
			'OFFERDATE' : self.OFFERDATE,
			'VERSIONNO' : self.VERSIONNO,
			'PARTICIPANTID' : self.PARTICIPANTID,
			'DAILYENERGYCONSTRAINT' : self.DAILYENERGYCONSTRAINT,
			'REBIDEXPLANATION' : self.REBIDEXPLANATION,
			'PRICEBAND1' : self.PRICEBAND1,
			'PRICEBAND2' : self.PRICEBAND2,
			'PRICEBAND3' : self.PRICEBAND3,
			'PRICEBAND4' : self.PRICEBAND4,
			'PRICEBAND5' : self.PRICEBAND5,
			'PRICEBAND6' : self.PRICEBAND6,
			'PRICEBAND7' : self.PRICEBAND7,
			'PRICEBAND8' : self.PRICEBAND8,
			'PRICEBAND9' : self.PRICEBAND9,
			'PRICEBAND10' : self.PRICEBAND10,
			'MINIMUMLOAD' : self.MINIMUMLOAD,
			'T1' : self.T1,
			'T2' : self.T2,
			'T3' : self.T3,
			'T4' : self.T4,
			'NORMALSTATUS' : self.NORMALSTATUS,
			'LASTCHANGED' : self.LASTCHANGED,
			'MR_FACTOR' : self.MR_FACTOR,
			'ENTRYTYPE' : self.ENTRYTYPE,
		}

class BidPerOffer(Document):
	
	SETTLEMENTDATE = DateTimeField()
	DUID = StringField()
	BIDTYPE = StringField()
	BIDSETTLEMENTDATE = DateTimeField()
	OFFERDATE = DateTimeField()
	PERIODID = StringField()
	VERSIONNO = IntField()
	MAXAVAIL = FloatField()
	FIXEDLOAD = FloatField()
	ROCUP = FloatField()
	ROCDOWN = FloatField()
	ENABLEMENTMIN = FloatField()
	ENABLEMENTMAX = FloatField()
	LOWBREAKPOINT = FloatField()
	HIGHBREAKPOINT = FloatField()
	BANDAVAIL1 = FloatField()
	BANDAVAIL2 = FloatField()
	BANDAVAIL3 = FloatField()
	BANDAVAIL4 = FloatField()
	BANDAVAIL5 = FloatField()
	BANDAVAIL6 = FloatField()
	BANDAVAIL7 = FloatField()
	BANDAVAIL8 = FloatField()
	BANDAVAIL9 = FloatField()
	BANDAVAIL10 = FloatField()
	LASTCHANGED = DateTimeField()
	PASAAVAILABILITY = FloatField()
	INTERVAL_DATETIME = DateTimeField()
	MR_CAPACITY = FloatField()
	rowhash = StringField(unique=True)

