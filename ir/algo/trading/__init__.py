import datetime
import sys
from builtins import set
from random import randint

import pika
import json
import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds
from os import listdir
from os.path import isfile, join

from ir.algo.trading.current_situation import CurrentStock, CurrentBudget, Order, Candidate

marketDataQueueName = 'algo-usr-rastak-rlc'
orderResponseQueueName = 'algo-usr-rastak-sle'
rabbitHost = '185.37.53.'
rabbitPort = 30672
rabbitUserName = 'algo-usr-rastak'
rabbitPassword = 'UVPP1R41X1I77MIJDPFO'
clientId = 'rastak'
clientSecret = 'LtywARien5jxwGUkgRSimFZ33uaGuQ'
user1Secret = 'pgun4Jn2Bgz43jd6WCeT9NRyGqa78Q'


class MyStrategy(bt.Strategy):
    params = dict(period=20)
    current_budget = -sys.maxint - 1
    current_orders = {}
    lot_amount = 6000000
    trackedIsins = ['', '']
    rsiCandidateIsins = ['IRO1HFRS0001']
    macDCandidateIsins = ['IRO1HFRS0001']
    atrCandidateIsins = [{'isin': 'IRO1HFRS0001', 'close': 1000, 'average': 20}]
    candidates = set(rsiCandidateIsins + macDCandidateIsins)
    portfolio = {}

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def _store_candidates(self):
        for isin in self.rsiCandidateIsins:
            candidate = Candidate(isin=isin, rsi=True)
            candidate.save()
        for isin in self.macDCandidateIsins:
            candidates = Candidate.objects(isin=isin)
            if len(candidates) > 0:
                candidate = candidates[0]
                candidate.macd = True
                candidate.save()
            else:
                candidate = Candidate(isin=isin, macd=True)
                candidate.save()

        for cand in self.atrCandidateIsins:
            candidates = Candidate.objects(isin=cand.isin)
            if len(candidates) > 0:
                candidate = candidates[0]
                candidate.atr = True
                candidate.atrAvg = cand.average
                candidate.atrClose = cand.close
                candidate.save()

    def fill_portfolio(self):
        stocks = CurrentStock.objects()
        for stock in stocks:
            self.portfolio.append(stock.isin, stock)

    def _main_init(self):
        self._store_candidates()
        self.fill_portfolio()
        self._channel_init()

    def _channel_init(self):
        credentials = pika.PlainCredentials(rabbitUserName, rabbitPassword)
        connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitHost, rabbitPort, '/', credentials))
        self.channel = connection.channel()
        self.channel.basic_consume(self.marketDataCallBack, queue=marketDataQueueName, no_ack=True)
        self.channel.basic_consume(self.orderNoticeCallBack, queue=orderResponseQueueName, no_ack=True)
        self.channel.start_consuming()

    def cancelOrder(self, orderId):
        self.channel.basic_publish(exchange='orderbox', routing_key='CANCEL',
                                   body=json.dumps({"orderId": orderId, "clientId": clientId}))

    def marketDataCallBack(self, ch, method, properties, body):
        try:
            # print(" [x] Market Data Received %r" % json.loads(body))
            jsonStr = json.loads(body)
            if 'instrumentId' in jsonStr:
                self._trade_event_process(jsonStr)
            elif 'lastTrade' in jsonStr:
                self.stock_watch_event(jsonStr)
            elif 'items' in jsonStr:
                self.bid_ask_event(jsonStr)
            elif 'individualBuyCount' in jsonStr:
                self.client_info_event(jsonStr)
        except ValueError as error:
            print(error)

    def _trade_event_process(self, jsonObject):
        # isin = jsonObject.isin
        # if isin not in self.portfolio:
        #     return
        # if isin in self.portfolio:
        #     stocks = CurrentStock.objects(isin=isin)
        #     if len(stocks) > 0:
        #         stock = stocks[0]
        #         if stock.maxValue < jsonObject.price:
        #             stock.maxValue = jsonObject.price
        #             stock.save()
        #         if jsonObject.price < stock.maxValue * .96:
        #             sell()
        return

    def stock_watch_event(self, jsonObject):
        isin = jsonObject.isin
        if isin not in self.candidates:
            if isin not in self.portfolio:
                return
        if isin in self.candidates:
            candidates = Candidate.objects(isin=isin)
            if len(candidates) > 0:
                candidate = candidates[0]
                # check bought volume of the stock
                if jsonObject.tradeVolume >= (candidate.volumeMax * 1.2):
                    candidate.volume = True
                    candidate.save()
                    self.check_buying_condition(candidate)
                # check
        if isin in self.portfolio:
            stocks = CurrentStock.objects(isin=isin)
            if len(stocks) > 0:
                stock = stocks[0]
                if stock.maxValue < jsonObject.close:
                    stock.maxValue = jsonObject.close
                    stock.save()
                if jsonObject.close < stock.maxValue * .96:
                    sell()

        return

    def client_info_event(self, jsonObject):
        isin = jsonObject.isin
        if isin not in self.candidates:
            return
        individualSellerCount = jsonObject.individualSellCount
        individualBuyerCount = jsonObject.individualBuyCount
        individualBuyVolume = jsonObject.individualBuyVolume
        if individualBuyerCount / individualSellerCount < .5 and individualBuyVolume > 100000:
            candidates = Candidate.objects(isin=isin)
            if len(candidates) > 0:
                candidate = candidates[0]
                candidate.indivCheck = True
                candidate.save()
                self.check_buying_condition(candidate)
                # if lots > 0:
                #     self.buy(isin, 1ots)
        return

    def check_buying_condition(self, candidate):
        lots = 0
        if candidate.volume:
            if candidate.rsi and candidate.macd and candidate.atr and candidate.indivCheck:
                lots = 5
            if candidate.rsi and candidate.macd and (candidate.atr or candidate.indivCheck):
                lots = 2
            if (candidate.rsi or candidate.macd) and (candidate.atr or candidate.indivCheck):
                lots = 1
        if lots > 0:
            return -1
        return 0

    def bid_ask_event(self, jsonObject):
        isin = jsonObject.isin
        if isin not in self.candidates:
            return
        candidates = Candidate.objects(isin=isin)
        if len(candidates) > 0:
            candidate = candidates[0]

    def orderNoticeCallBack(self, ch, method, properties, json):
        print(" [x] Order Notice Received %r" % json)
        body = json.loads(json)
        if body.state == 'EXECUTED':
            current_situation[body.isin] = body.amount
            currentStock = CurrentStock(isin=body.isin, maxValue=body.price, valume=body.vol)
            currentStock.save()
            self.candidates.remove(body.isin)
            del self.current_orders[body.orderId]
            Order.delete(orderId=body.orderId)
        elif body.state == 'ERROR':
            del self.current_orders[body.orderId]
            self._order_failure_handler(body.isin, body.value)
            Order.delete(orderId=body.orderId)
            

    def __init__(self):
        # sma = btind.SimpleMovingAverage(self.datas[0], period=self.params.period)
        # sma = btind.SimpleMovinAverage(self.data, period=20)
        self.sma = sma = btind.SMA(self.data, period=20)
        self.rsi = rsi = btind.RSI_SMA(self.data.close, period=21)

        # close_over_sma = self.data.close > sma
        # sma_dist_to_high = self.data.high - sma

        # sma_dist_small = sma_dist_to_high < 3.5

        # Unfortunately "and" cannot be overridden in Python being
        # a language construct and not an operator and thus a
        # function has to be provided by the platform to emulate it

        # sell_sig = bt.And(close_over_sma, sma_dist_small)
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

    def _list_stocks(self, path):
        self.files = [f for f in listdir(path) if isfile(join(path, f))]

    def _trailing_stop_checker(isin, value):
        stocks = CurrentStock.objects(isin=isin)
        if len(stocks) > 0:
            stock = stocks[0]
            if stock.maxValue < value:
                stock.maxValue = value
                stock.save()
                return False
            elif stock.maxValue * .93 > value:
                return True
        return False

    def _order_failure_handler(self, isin, value):
        budget = CurrentBudget.objects()
        budget.availableBudget += value
        budget.save()
        order = Order.find(isin=isin)
        order.situation = 1
        order.save()

    def buy(self, isin, lots):
        budget = CurrentBudget.objects()
        amount = self.lot_amount * lots
        budget.availableBudget -= amount
        budget.save()
        self._create_order(req_isin=isin, budget=amount, side="BUY")

    def sell(self, isin, price):
        # budget = CurrentBudget.objects()
        # amount = self.lot_amount * lots
        # budget.availableBudget -= amount
        # budget.save()
        self._create_order(req_isin=isin, price=price, side="SELL")

    def _create_order(self, req_isin, budget, price, quantity, side):
        orderId = randint(100000, 999999)
        order = Order(budget=budget, isin=req_isin, situation=0, side=side, orderId=orderId)
        order.save()
        self.current_orders[req_isin] = quantity
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
                "senderOrderId": orderId
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

    def track_the_trace(self, isin, ):

        return


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
