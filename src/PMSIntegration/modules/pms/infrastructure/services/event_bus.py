import pika
import json
import os

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
ENABLE_EVENTS = os.getenv("ENABLE_EVENTS", "false").lower() == "true"

EVENT_EXCHANGE = "travelhub.events.exchange"


class EventBus:

    def publish_event(self, routing_key, event_type, payload):

        if not ENABLE_EVENTS:
            print(f"[DEV MODE] Event not sent: {routing_key} -> {payload}")
            return

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBIT_HOST)
        )

        channel = connection.channel()

        message = {
            "eventType": event_type,
            **payload
        }

        channel.exchange_declare(
            exchange=EVENT_EXCHANGE,
            exchange_type="topic",
            durable=True
        )

        channel.basic_publish(
            exchange=EVENT_EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        connection.close()