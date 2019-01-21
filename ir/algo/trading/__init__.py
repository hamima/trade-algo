from builtins import set
from random import randint
from mongoengine import *

import pika
import json

from ir.algo.trading.current_situation import CurrentStock, CurrentBudget, Order, Candidate

marketDataQueueName = 'algo-usr-rastak-rlc'
orderResponseQueueName = 'algo-usr-rastak-sle'
rabbitHost = '185.37.53.'
rabbitPort = 30672
rabbitUserName = 'algo-usr-rastak'
rabbitPassword = 'UVPP1R41X1I77MIJDPFO'
clientId = 'LtywARien5jxwGUkgRSimFZ33uaGuQ'
clientSecret = 'LtywARien5jxwGUkgRSimFZ33uaGuQ'
user1Secret = 'pgun4Jn2Bgz43jd6WCeT9NRyGqa78Q'


class MyStrategy():
    # params = dict(period=20)
    # current_budget = -sys.maxint - 1
    lot_amount = 3000000
    # trackedIsins = ['', '']
    rsiIsins = {
        "IRO1ATIR0001": {"close": 4513, "maxVol": 4400851, "atr": 195},
        "IRO3OSHZ0001": {"close": 1367, "maxVol": 3193025, "atr": 55},
        "IRO1BHMN0001": {"close": 1074, "maxVol": 18050543, "atr": 33},
        "IRO1SHZG0001": {"close": 6354, "maxVol": 1781598, "atr": 300},
        "IRO1JAMD0001": {"close": 8738, "maxVol": 130593, "atr": 340},
        "IRO3BMAZ0001": {"close": 13500, "maxVol": 420100, "atr": 600},
        "IRO1RSAP0001": {"close": 1346, "maxVol": 39520936, "atr": 53},
        "IRO1RINM0001": {"close": 2051, "maxVol": 5055583, "atr": 106},
        "IRO1LMIR0001": {"close": 4316, "maxVol": 3919574, "atr": 168},
        "IRO1RADI0001": {"close": 2564, "maxVol": 587690, "atr": 80},
        "IRO1MSTI0001": {"close": 3340, "maxVol": 3148506, "atr": 170},
        "IRO1KHSH0001": {"close": 1860, "maxVol": 3943163, "atr": 65}
    }
    crossoverIsins = {
        "IRO1TAYD0001": {"close": 4400, "maxVol": 4740612, "atr": 210},
        "IRO1SIMS0001": {"close": 1288, "maxVol": 1032321, "atr": 52},
        "IRO1TBAS0001": {"close": 5239, "maxVol": 1133920, "atr": 279},
        "IRO1SEFH0001": {"close": 5952, "maxVol": 37418, "atr": 267},
        "IRO1SSOF0001": {"close": 2403, "maxVol": 1435683, "atr": 117},
        "IRO1SSNR0001": {"close": 15181, "maxVol": 76711, "atr": 660},
        "IRO3DZLZ0001": {"close": 3460, "maxVol": 3606178, "atr": 140},
        "IRO1KHOC0001": {"close": 4051, "maxVol": 3060212, "atr": 164},
        "IRO1DSOB0001": {"close": 2701, "maxVol": 8375651, "atr": 120},
        "IRO1RINM0001": {"close": 2051, "maxVol": 5055583, "atr": 106},
        "IRO3BIPZ0001": {"close": 4371, "maxVol": 11026429, "atr": 220},
        "IRO1BAHN0001": {"close": 7487, "maxVol": 3551976, "atr": 349},
        "IRO1SKAZ0001": {"close": 3077, "maxVol": 2193869, "atr": 132},
        "IRO1LSMD0001": {"close": 1440, "maxVol": 2007496, "atr": 57}
    }
    rsiCandidateIsins = []
    macDCandidateIsins = []
    # atrCandidateIsins = [{'isin': 'IRO1HFRS0001', 'close': 1000, 'average': 20}]
    candidates = set()
    portfolio = []
    noTrades = 0
    isForbidden = False

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def _store_candidates(self):
        for isin, v in self.rsiIsins.items():
            self.rsiCandidateIsins.append(isin)
            candidate = Candidate(isin=isin, rsi=True, atrAvg=v["atr"], atrClose=v["close"], volumeMax=v["maxVol"])
            candidate.save()
        for isin, v in self.crossoverIsins.items():
            self.macDCandidateIsins.append(isin)
            candidates = Candidate.objects(isin=isin)
            if len(candidates) > 0:
                candidate = candidates[0]
                candidate.macd = True
                candidate.save()
            else:
                candidate = Candidate(isin=isin, rsi=True, atrAvg=v["atr"], atrClose=v["close"], volumeMax=v["maxVol"])
                candidate.save()
        self.candidates.update(self.rsiCandidateIsins)
        self.candidates.update(self.macDCandidateIsins)

    def fill_portfolio(self):
        stocks = CurrentStock.objects()
        for stock in stocks:
            self.portfolio.append(stock.isin, stock)

    def _main_init(self):
        self._mongo_init()
        self._store_candidates()
        self.fill_portfolio()
        self.budget_init()
        self._channel_init()

    def budget_init(self):
        budget = CurrentBudget.objects()
        if len(budget) == 0:
            budget = CurrentBudget(availableBudget=10000000)
            budget.save()

    def _mongo_init(self):
        connect("trading_db")

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
            # if 'instrumentId' in jsonStr:
            #   self._trade_event_process(jsonStr)
            if 'lastTrade' in jsonStr:
                self.stock_watch_event(jsonStr)
            elif 'items' in jsonStr:
                self.bid_ask_event(jsonStr)
            elif 'individualBuyCount' in jsonStr:
                self.client_info_event(jsonStr)
        except ValueError as error:
            print(error)

    def stock_watch_event(self, jsonObject):
        isin = jsonObject.isin
        if isin not in self.candidates:
            if isin not in self.portfolio:
                return
        if isin in self.candidates:
            print(" [x] Market Data (StockWatch) of candidate Received %r" % jsonObject)
            candidates = Candidate.objects(isin=isin)
            if len(candidates) > 0:
                candidate = candidates[0]
                # check bought volume of the stock
                if jsonObject.tradeVolume >= (candidate.volumeMax * 1.2):
                    candidate.volume = True
                    candidate.save()
                    self._check_buying_condition(candidate)
                # check ATR
                if max(jsonObject.high - candidate.atrClose,
                       jsonObject.high - jsonObject.low) >= 1.5 * candidate.atrAvg:
                    candidate.atr = True
                    candidate.save()
                    self._check_buying_condition(candidate)
        if isin in self.portfolio:
            print(" [x] Market Data (StockWatch) of portfolio Received %r" % jsonObject)
            stocks = CurrentStock.objects(isin=isin)
            if len(stocks) > 0:
                stock = stocks[0]
                if stock.maxValue < jsonObject.close:
                    stock.maxValue = jsonObject.close
                    stock.save()
                if jsonObject.close < stock.maxValue * .96:
                    self.sell(isin)

    def sell(self, isin):
        if self.isForbidden:
            return
        stocks = CurrentStock.objects(isin=isin)
        if len(stocks) > 0:
            stock = stocks[0]
            print('Sell ISIN %s for Quantity %s and Price %s' % (isin, stock.volume, stock.sellPrice - 1))
            self._create_order(req_isin=isin, price=stock.sellPrice - 1, side="SELL", quantity=stock.volume)

    def client_info_event(self, jsonObject):
        isin = jsonObject.isin
        if isin not in self.candidates:
            return
        print(" [x] Market Data (ClientInfo) of candidate Received %r" % jsonObject)
        individualSellerCount = jsonObject.individualSellCount
        individualBuyerCount = jsonObject.individualBuyCount
        individualBuyVolume = jsonObject.individualBuyVolume
        if individualBuyerCount / individualSellerCount < .5 and individualBuyVolume > 100000:
            candidates = Candidate.objects(isin=isin)
            if len(candidates) > 0:
                candidate = candidates[0]
                candidate.indivCheck = True
                candidate.save()
                self._check_buying_condition(candidate)

    def _check_buying_condition(self, candidate):
        if self.isForbidden:
            return
        lots = 0
        if candidate.volume:
            if candidate.rsi and candidate.macd and candidate.atr and candidate.indivCheck:
                lots = 5
            if candidate.rsi and candidate.macd and (candidate.atr or candidate.indivCheck):
                lots = 2
            if (candidate.rsi or candidate.macd) and (candidate.atr or candidate.indivCheck):
                lots = 1
        if lots > 0:
            price = candidate.buyPrice + 1
            quantity = lots * self.lot_amount / price
            print('Buy ISIN %s for Quantity %s and Price %s' % (candidate.isin, quantity, price))
            self._create_order(req_isin=candidate.isin, price=price, side="BUY", quantity=quantity)
            budgets = CurrentBudget.objects()
            if len(budgets):
                budget = budgets[0]
                budget -= lots * self.lot_amount
                budget.save()

    def bid_ask_event(self, jsonObject):
        isin = jsonObject.isin
        if isin in self.candidates:
            print(" [x] Market Data (BidAsk) of candidate Received %r" % jsonObject)
            items = jsonObject.items
            candidates = Candidate.objects(isin=isin)
            if len(candidates) > 0:
                candidate = candidates[0]
                candidate.price = items[0].bidPrice
                candidate.save()

        if isin in self.portfolio:
            print(" [x] Market Data (BidAsk) of portfolio Received %r" % jsonObject)
            items = jsonObject.items
            stocks = CurrentStock.objects(isin=isin)
            if len(stocks) > 0:
                stock = stocks[0]
                stock.sellPrice = items[0].askPrice
                stock.save()

    def orderNoticeCallBack(self, ch, method, properties, json):
        print(" [x] Order Notice Received %r" % json)
        body = json.loads(json)
        if body.state == 'EXECUTED':
            self.noTrades += 1
            self.candidates.remove(body.isin)
            if body.side == 'BUY':
                currentStock = CurrentStock(isin=body.isin, maxValue=body.price, valume=body.vol)
                currentStock.save()
            else:
                CurrentStock.delete(isin=body.isin)
            if self.noTrades > 3:
                self.isForbidden = True
            Order.delete(orderId=body.senderOrderId)
        elif body.state == 'ERROR':
            self._order_failure_handler(body.isin, body)

    def __init__(self):
        self._main_init()
        # sma = btind.SimpleMovingAverage(self.datas[0], period=self.params.period)
        # sma = btind.SimpleMovinAverage(self.data, period=20)
        # self.sma = sma = btind.SMA(self.data, period=20)
        # self.rsi = rsi = btind.RSI_SMA(self.data.close, period=21)

        # close_over_sma = self.data.close > sma
        # sma_dist_to_high = self.data.high - sma

        # sma_dist_small = sma_dist_to_high < 3.5

        # Unfortunately "and" cannot be overridden in Python being
        # a language construct and not an operator and thus a
        # function has to be provided by the platform to emulate it

        # sell_sig = bt.And(close_over_sma, sma_dist_small)
        # self._channel_init()

    def _order_failure_handler(self, isin, jsonObject):
        budget = CurrentBudget.objects()
        budget.availableBudget += jsonObject.price * jsonObject.quantity
        budget.save()
        Order.delete(isin=isin)

    # def buy(self, isin, lots):
    #     budget = CurrentBudget.objects()
    #     amount = self.lot_amount * lots
    #     budget.availableBudget -= amount
    #     budget.save()
    #     self._create_order(req_isin=isin, budget=amount, side="BUY")

    def _create_order(self, req_isin, price, quantity, side):
        orderId = randint(100000, 999999)
        order = Order(isin=req_isin, situation=0, side=side, orderId=orderId)
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


strategy = MyStrategy()

'''
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
'''

'''
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
'''
# cerebro = bt.Cerebro()
# data = btfeeds.feed
# cerebro.adddata(_read_data('IRO1BMLT0007.csv'))
# cerebro.broker.setcash(10000000.0)

# Set the commission - 0.1% ... divide by 100 to remove the %
# cerebro.broker.setcommission(commission=0.001)
# cerebro.addstrategy(MyStrategy, period=30)
# cerebro.run()
# Print out the final result
# print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

# cerebro.plot()
