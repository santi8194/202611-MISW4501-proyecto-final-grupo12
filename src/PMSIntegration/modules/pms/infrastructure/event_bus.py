import pika
import json
import os

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
ENABLE_EVENTS = os.getenv("ENABLE_EVENTS", "false").lower() == "true"

COMMAND_EXCHANGE = "travelhub.commands.exchange"
EVENT_EXCHANGE = "travelhub.events.exchange"


class EventBus:

    def publish_event(self, routing_key, payload):

        if not ENABLE_EVENTS:
            print(f"[DEV MODE] Event not sent: {routing_key} -> {payload}")
            return

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBIT_HOST)
        )

        channel = connection.channel()

        channel.exchange_declare(
            exchange=EVENT_EXCHANGE,
            exchange_type="topic",
            durable=True
        )

        channel.basic_publish(
            exchange=EVENT_EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload)
        )

        connection.close()


    def publish_command(self, routing_key, payload):

        if not ENABLE_EVENTS:
            print(f"[DEV MODE] Command not sent: {routing_key} -> {payload}")
            return

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBIT_HOST)
        )

        channel = connection.channel()

        channel.exchange_declare(
            exchange=COMMAND_EXCHANGE,
            exchange_type="direct",
            durable=True
        )

        channel.basic_publish(
            exchange=COMMAND_EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload)
        )

        connection.close()