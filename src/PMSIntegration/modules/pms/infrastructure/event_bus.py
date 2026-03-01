import pika
import json
import os

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
ENABLE_EVENTS = os.getenv("ENABLE_EVENTS", "false").lower() == "true"

class EventBus:

    def publish(self, event_name, payload):

        if not ENABLE_EVENTS:
            print(f"[DEV MODE] Event not sent: {event_name} -> {payload}")
            return

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBIT_HOST)
        )

        channel = connection.channel()
        channel.exchange_declare(
            exchange='saga_exchange',
            exchange_type='fanout'
        )

        channel.basic_publish(
            exchange='saga_exchange',
            routing_key='',
            body=json.dumps({
                "event": event_name,
                "data": payload
            })
        )

        connection.close()