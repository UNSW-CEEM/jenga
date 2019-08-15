from mongoengine import *

class Demand(Document):
    date_time = DateTimeField(indexed=True)
    demand = FloatField()
    region = StringField(indexed=True)