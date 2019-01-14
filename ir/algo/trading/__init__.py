import datetime
import sys
import pika
import json
import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds

from ir.algo.trading.current_situation import CurrentStock, CurrentBudget, Order



marketDataQueueName = 'algo-usr-?-rlc'
orderResponseQueueName = 'algo-usr-?-sle'
rabbitHost = '185.37.53.198'
rabbitPort = 30672
rabbitUserName = ''
rabbitPassword = ''
clientId = ''
user1Secret = ''



class MyStrategy(bt.Strategy):
    params = dict(period=20)
    current_budget = -sys.maxint - 1

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))
    def _channel_init(self):
        credentials = pika.PlainCredentials(rabbitUserName, rabbitPassword)
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitHost, rabbitPort, '/', credentials))
        self.channel = connection.channel()

    # def _create_order(self, req_isin, budget):

        # sendOrder(req_isin = 'IRO1SIPA0001', 1381, 1, 'BUY')
        # cancelOrder(54321)

        # un-comment to receive Market Data
        # self.channel.basic_consume(marketDataCallBack, queue=marketDataQueueName, no_ack=True)

        # Setup Order Changes Listener
        # self.channel.basic_consume(orderNoticeCallBack, queue=orderResponseQueueName, no_ack=True)

        # Start Listening to all data
        self.channel.start_consuming()

    def cancelOrder(self, orderId):
        self.channel.basic_publish(exchange='orderbox', routing_key='CANCEL', body=json.dumps({"orderId": orderId, "clientId": clientId}))


    def marketDataCallBack(self, ch, method, properties, body):
        print(" [x] Market Data Received %r" % json.loads(body))


    def orderNoticeCallBack(self, ch, method, properties, body):
        print(" [x] Order Notice Received %r" % body)


    def __init__(self):
        # sma = btind.SimpleMovingAverage(self.datas[0], period=self.params.period)
        # sma = btind.SimpleMovinAverage(self.data, period=20)
        self.sma = sma = btind.SMA(self.data, period=20)
        self.rsi = rsi = btind.RSI_SMA(self.data.close, period=21)

        close_over_sma = self.data.close > sma
        sma_dist_to_high = self.data.high - sma

        sma_dist_small = sma_dist_to_high < 3.5

        # Unfortunately "and" cannot be overridden in Python being
        # a language construct and not an operator and thus a
        # function has to be provided by the platform to emulate it

        sell_sig = bt.And(close_over_sma, sma_dist_small)
        self._channel_init()

    def next(self):

        # Although this does not seem like an "operator" it actually is
        # in the sense that the object is being tested for a True/False
        # response

        if self.sma > 30.0:
            print('sma is greater than 30.0')

        if self.sma > self.data.close:
            print('sma is above the close price')

        if self.sell_sig:  # if sell_sig == True: would also be valid
            print('sell sig is True')
        else:
            print('sell sig is False')

        if self.sma_dist_to_high > 5.0:
            print('distance from sma to hig is greater than 5.0')

    @staticmethod
    def _trailing_stop_checker(isin, value):
        stock = CurrentStock.objects(isin=isin)
        if stock is not None:
            if stock.maxValue < value:
                stock.maxValue = value
                stock.save()
                return False
            elif stock.maxValue * .93 > value:
                return True
        return False

    def buy(self, isin):
        budget = CurrentBudget.objects()
        budget.availableBudget = budget.availableBudget * .02

        self._create_order(req_isin=isin, budget=budget.availableBudget * .02)

    def _create_order(self, req_isin, budget, price, quantity, side ):
        order = Order(budget=budget, isin=req_isin, situation=0)
        order.save()
        self.channel.basic_publish(exchange='orderbox', routing_key='ORDER', body=json.dumps(
        {
            "userId": user1Secret,
            "clientId": clientId,
            "isin": req_isin,
            "broker": "PASARGAD",
            "iceberg": 0,
            "price": price,
            "quantity": quantity,
            "side": side,
            "validity": 'DAY',
            "tag": 'TAG_TAG',
            "senderOrderId": 101010
        })
                          )

        return order

    def _get_price(self, isin):

        return 0

def _read_data(datapath):
    dateformat = '%Y%m%d'

    data = bt.feeds.GenericCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(2009, 2, 21),
        todate=datetime.datetime(2011, 5, 14),
        nullvalue=0.0,
        dtformat=dateformat,
        datetime=1,
        high=3,
        low=4,
        open=2,
        close=5,
        volume=6,
        openinterest=-1
    )
    return data


cerebro = bt.Cerebro()
data = btfeeds.feed
cerebro.adddata(_read_data('IRO1BMLT0007.csv'))
cerebro.broker.setcash(10000000.0)

# Set the commission - 0.1% ... divide by 100 to remove the %
cerebro.broker.setcommission(commission=0.001)
cerebro.addstrategy(MyStrategy, period=30)
cerebro.run()
# Print out the final result
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

cerebro.plot()
