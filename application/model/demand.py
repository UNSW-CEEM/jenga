from mongoengine import *

class Demand(Document):
    date_time = DateTimeField()
    demand = FloatField()
    region = StringField()