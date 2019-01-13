import pika






def setup():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='ip_address'))
    channel = connection.channel()
    channel.queue_declare(queue='rlc-queue-name')
    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)
    channel.basic_consume(callback, queue='rlc-queue-name', no_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
