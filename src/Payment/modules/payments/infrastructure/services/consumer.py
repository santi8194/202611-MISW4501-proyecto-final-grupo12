import json
from config.rabbitmq import create_connection
from modules.payments.infrastructure.services.handlers import handle_process_payment

COMMANDS_EXCHANGE = "travelhub.commands.exchange"
QUEUE_NAME = "payment.commands.queue"
ROUTING_KEY = "cmd.payment.procesar-pago"


def callback(ch, method, properties, body):

    data = json.loads(body.decode())

    print("Comando recibido:", data)

    try:

        handle_process_payment(data)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:

        print("Error procesando comando:", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consumer():

    connection = create_connection()
    channel = connection.channel()

    channel.exchange_declare(
        exchange=COMMANDS_EXCHANGE,
        exchange_type="direct",
        durable=True
    )

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    channel.queue_bind(
        exchange=COMMANDS_EXCHANGE,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY
    )

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )

    print("Listening on queue:", QUEUE_NAME)
    channel.start_consuming()