from mongoengine import *
import config

connect(config.DB_NAME, host=config.MONGO_HOST,username=config.MONGO_USER, password=config.MONGO_PASSWORD, authentication_source=config.MONGO_AUTH_SOURCE)

class DispatchLoad(Document):
    SETTLEMENTDATE = DateTimeField()	 # Market date and time starting at 04:05 	DATE
    RUNNO = FloatField() # Dispatch run no; always 1 	NUMBER(3,0)
    DUID = StringField() # Dispatchable unit identifier 	VARCHAR2(10)
    TRADETYPE = IntField() # Not used 	NUMBER(2,0)
    DISPATCHINTERVAL = StringField() # Dispatch period identifier, from 001 to 288 in format YYYYMMDDPPP. 	NUMBER(22,0)
    INTERVENTION = IntField() # Intervention flag if intervention run 	NUMBER(2,0)
    CONNECTIONPOINTID = StringField() # Connection point identifier for DUID 	VARCHAR2(12)
    DISPATCHMODE = IntField() # Dispatch mode for fast start plant (0 to 4). 	NUMBER(2,0)
    AGCSTATUS = IntField() # AGC Status from EMS* 1 = on* 0 = off 	NUMBER(2,0)
    INITIALMW = FloatField() # Initial MW at start of period 	NUMBER(15,5)
    TOTALCLEARED = FloatField() # Target MW for end of period 	NUMBER(15,5)
    RAMPDOWNRATE = FloatField() # Ramp down rate used in dispatch (lesser of bid or telemetered rate). 	NUMBER(15,5)
    RAMPUPRATE = FloatField() # Ramp up rate (lesser of bid or telemetered rate). 	NUMBER(15,5)
    LOWER5MIN = FloatField() # Lower 5 min reserve target 	NUMBER(15,5)
    LOWER60SEC = FloatField() # Lower 60 sec reserve target 	NUMBER(15,5)
    LOWER6SEC = FloatField() # Lower 6 sec reserve target 	NUMBER(15,5)
    RAISE5MIN = FloatField() # Raise 5 min reserve target 	NUMBER(15,5)
    RAISE60SEC = FloatField() # Raise 60 sec reserve target 	NUMBER(15,5)
    RAISE6SEC = FloatField() # Raise 6 sec reserve target 	NUMBER(15,5)
    DOWNEPF = FloatField() # Not Used 	NUMBER(15,5)
    UPEPF = FloatField() # Not Used 	NUMBER(15,5)
    MARGINAL5MINVALUE = FloatField() # Marginal $ value for 5 min 	NUMBER(15,5)
    MARGINAL60SECVALUE = FloatField() # Marginal $ value for 60 seconds 	NUMBER(15,5)
    MARGINAL6SECVALUE = FloatField() # Marginal $ value for 6 seconds 	NUMBER(15,5)
    MARGINALVALUE = FloatField() # Marginal $ value for energy 	NUMBER(15,5)
    VIOLATION5MINDEGREE = FloatField() # Violation MW 5 min 	NUMBER(15,5)
    VIOLATION60SECDEGREE = FloatField() # Violation MW 60 seconds 	NUMBER(15,5)
    VIOLATION6SECDEGREE = FloatField() # Violation MW 6 seconds 	NUMBER(15,5)
    VIOLATIONDEGREE = FloatField() # Violation MW energy 	NUMBER(15,5)
    LASTCHANGED = DateTimeField() # Last date and time record changed 	DATE
    LOWERREG = FloatField() # Lower Regulation reserve target 	NUMBER(15,5)
    RAISEREG = FloatField() # Raise Regulation reserve target 	NUMBER(15,5)
    AVAILABILITY = FloatField() # Bid energy availability 	NUMBER(15,5)
    RAISE6SECFLAGS = IntField() # Raise 6sec status flag - see 	NUMBER(3,0)
    RAISE60SECFLAGS = IntField() # Raise 60sec status flag - see 	NUMBER(3,0)
    RAISE5MINFLAGS = IntField() # NUMBER(3,0)
    RAISEREGFLAGS = IntField() # Raise Reg status flag - see 	NUMBER(3,0)
    LOWER6SECFLAGS = IntField() # Lower 6sec status flag - see 	NUMBER(3,0)
    LOWER60SECFLAGS = IntField() # Lower 60sec status flag 	NUMBER(3,0)
    LOWER5MINFLAGS = IntField() # Lower 5min status flag 	NUMBER(3,0)
    LOWERREGFLAGS = IntField() # Lower Reg status flag - see 	NUMBER(3,0)
    RAISEREGAVAILABILITY = FloatField() # RaiseReg availability - minimum of bid and telemetered value 	NUMBER(15,5)
    RAISEREGENABLEMENTMAX = FloatField() # RaiseReg enablement max point - minimum of bid and telemetered value 	NUMBER(15,5)
    RAISEREGENABLEMENTMIN = FloatField() # RaiseReg Enablement Min point - maximum of bid and telemetered value 	NUMBER(15,5)
    LOWERREGAVAILABILITY = FloatField() # Lower Reg availability - minimum of bid and telemetered value 	NUMBER(15,5)
    LOWERREGENABLEMENTMAX = FloatField() # Lower Reg enablement Max point - minimum of bid and telemetered value 	NUMBER(15,5)
    LOWERREGENABLEMENTMIN = FloatField() # Lower Reg Enablement Min point - maximum of bid and telemetered value 	NUMBER(15,5)
    RAISE6SECACTUALAVAILABILITY = FloatField() # trapezium adjusted raise 6sec availability 	NUMBER(16,6)
    RAISE60SECACTUALAVAILABILITY = FloatField() # trapezium adjusted raise 60sec availability 	NUMBER(16,6)
    RAISE5MINACTUALAVAILABILITY = FloatField() # trapezium adjusted raise 5min availability 	NUMBER(16,6)
    RAISEREGACTUALAVAILABILITY = FloatField() # trapezium adjusted raise reg availability 	NUMBER(16,6)
    LOWER6SECACTUALAVAILABILITY = FloatField() # trapezium adjusted lower 6sec availability 	NUMBER(16,6)
    LOWER60SECACTUALAVAILABILITY = FloatField() # trapezium adjusted lower 60sec availability 	NUMBER(16,6)
    LOWER5MINACTUALAVAILABILITY = FloatField() # trapezium adjusted lower 5min availability 	NUMBER(16,6)
    LOWERREGACTUALAVAILABILITY = FloatField() # trapezium adjusted lower reg availability 	NUMBER(16,6)
    rowhash = StringField(unique=True)
    meta = {
        'indexes': [
            'DUID',
            'SETTLEMENTDATE',
        ]
    }