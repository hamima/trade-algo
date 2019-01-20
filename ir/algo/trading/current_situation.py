from mongoengine import *
import datetime


class CurrentStock(DynamicDocument):
    isin = StringField(required=True)
    txDate = DateField(default=datetime.datetime.utcnow)
    maxValue = IntField()
    boughtValue = IntField()
    volume = LongField()
    sellPrice = IntField()
    meta = {'collection': 'CurrentStock'}


class CurrentBudget(DynamicDocument):
    availableBudget = LongField()
    meta = {'collection': 'CurrentBudget'}


class Order(DynamicDocument):
    budget = LongField()
    isin = StringField()
    side = StringField()
    orderId = StringField()
    situation = IntField(min_value=0, max_value=2)
    meta = {'collection': 'Order'}

class Candidate(DynamicDocument):
    isin = StringField()
    rsi = BooleanField()
    macd = BooleanField()
    atr = BooleanField()
    atrClose = IntField()
    atrAvg = IntField()
    volumeMax = LongField()
    volume = BooleanField()
    indivCheck = BooleanField()
    buyPrice = IntField()
    meta = {'collection': 'Candidate'}
