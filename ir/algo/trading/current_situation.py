from mongoengine import *
import datetime


class CurrentStock(DynamicDocument):
    isin = StringField(required=True)
    txDate = DateField(default=datetime.datetime.utcnow)
    maxValue = IntField()
    boughtValue = IntField()
    volume = LongField()
    meta = {'collection': 'CurrentStock'}


class CurrentBudget(DynamicDocument):
    availableBudget = LongField()
    meta = {'collection': 'CurrentBudget'}


class Order(DynamicDocument):
    budget = LongField()
    isin = StringField()
    situation = IntField(min_value=0, max_value=2)
    meta = {'collection': 'Order'}


class StockWatchEvent:
    isin = None
    last = None
    closing = None
    first = None
    high = None
    low = None
    min = None
    max = None
    tardeValue = None
    tradeVolume = None
    tradesCount = None
    referencePrice = None
    state = None
    event = None
    upRangeCount = None
    downRangeCount = None
    lastTrade = None

