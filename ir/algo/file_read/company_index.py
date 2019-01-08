from mongoengine import *
import datetime


class CompanyDailyIndex(DynamicDocument):
    indicator = StringField(required=True)
    tx_date = DateField(default=datetime.datetime.utcnow)
    open_value = IntField()
    high_value = IntField()
    low_value = IntField()
    close_value = IntField()
    vol = LongField()
    meta = {'collection': 'company'}

    def to_string(self):
        print(self.indicator, ', ', self.open_value)
