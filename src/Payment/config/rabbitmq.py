import pika
import json

RABBIT_HOST = "localhost"
EXCHANGE = "travelhub.exchange"

def get_connection():
    return pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST)
    )

def publish_event(routing_key, message):
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic")

    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(message)
    )

    connection.close()