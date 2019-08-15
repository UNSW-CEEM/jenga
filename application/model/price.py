from mongoengine import *

class Price(Document):
    date_time = DateTimeField(indexed=True)
    price = FloatField()
    region = StringField(indexed=True)
    price_type = StringField(indexed=True)

    