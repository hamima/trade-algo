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
    side = StringFiled()
    situation = IntField(min_value=0, max_value=2)
    meta = {'collection': 'Order'}


