import pika
import json
import os
from config.rabbitmq import create_connection

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
ENABLE_EVENTS = os.getenv("ENABLE_EVENTS", "false").lower() == "true"

EVENT_EXCHANGE = "travelhub.events.exchange"

class EventBus:

    def publish_event(self, routing_key, event_type, payload):

        connection = None
        try:
            connection = create_connection()
            channel = connection.channel()

            channel.exchange_declare(
                exchange=EVENT_EXCHANGE,
                exchange_type="topic",
                durable=True
            )

            message = {
                "type": event_type,
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

            print(f"[{event_type}] Publicado a {routing_key} sobre {EVENT_EXCHANGE}")
        except Exception as e:
            print(f"Error publicando evento {event_type}:", e)
        finally:
            if connection and connection.is_open:
                connection.close()