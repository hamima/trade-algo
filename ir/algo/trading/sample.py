#!/usr/bin/env python
import pika
import json

marketDataQueueName = 'algo-usr-rastak-rlc'
orderResponseQueueName = 'algo-usr-rastak-sle'
rabbitHost = '185.37.53.'
rabbitPort = 30672
rabbitUserName = 'algo-usr-rastak'
rabbitPassword = 'UVPP1R41X1I77MIJDPFO'
clientId = 'rastak'
clientSecret = 'LtywARien5jxwGUkgRSimFZ33uaGuQ'
user1Secret = 'pgun4Jn2Bgz43jd6WCeT9NRyGqa78Q'
isin = 'IRO1HFRS0001'


# side possible values : BUY | SELL
# validity posible values DAY | FILL_AND_KILL
def sendOrder(isin, quantity, price, side):
    channel.basic_publish(exchange='orderbox', routing_key='ORDER', body=json.dumps(
        {
            "userId": user1Secret,
            "clientId": clientId,
            "isin": isin,
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


def cancelOrder(orderId):
    channel.basic_publish(exchange='orderbox', routing_key='CANCEL',
                          body=json.dumps({"orderId": orderId, "clientId": clientId}))


def marketDataCallBack(ch, method, properties, body):
    print(" [x] Market Data Received %r" % json.loads(body))


def orderNoticeCallBack(ch, method, properties, body):
    print(" [x] Order Notice Received %r" % body)


# Connecting To Server
credentials = pika.PlainCredentials(rabbitUserName, rabbitPassword)
connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitHost, rabbitPort, '/', credentials))
channel = connection.channel()

sendOrder(isin, 150, 15680, 'BUY')
# cancelOrder(54321)

# un-comment to receive Market Data
channel.basic_consume(marketDataCallBack, queue=marketDataQueueName, no_ack=True)

# Setup Order Changes Listener
channel.basic_consume(orderNoticeCallBack, queue=orderResponseQueueName, no_ack=True)

# Start Listening to all data
channel.start_consuming()
