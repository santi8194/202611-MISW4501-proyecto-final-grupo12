import pika
import time
from config.settings import settings

def create_connection():
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER,
        settings.RABBITMQ_PASS
    )

    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        credentials=credentials
    )

    for attempt in range(10):
        try:
            print(f"Connecting to RabbitMQ (attempt {attempt+1})...")
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready, retrying in 5 seconds...")
            time.sleep(5)

    raise Exception("Could not connect to RabbitMQ after retries")