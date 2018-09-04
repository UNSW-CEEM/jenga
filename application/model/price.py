from mongoengine import *

class Price(Document):
    date_time = DateTimeField()
    price = FloatField()
    region = StringField()
    price_type = StringField()

    