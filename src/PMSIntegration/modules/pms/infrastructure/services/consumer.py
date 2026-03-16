import json
from config.rabbitmq import create_connection

from modules.pms.infrastructure.services.handlers import handle_confirm_reservation, handle_cancel_reservation

COMMANDS_EXCHANGE = "travelhub.commands.exchange"
QUEUE_NAME = "pms.commands.queue"
ROUTING_KEY_CONFIRM = "cmd.pms.confirmar-reserva"
ROUTING_KEY_CANCEL = "cmd.pms.cancelar-reserva"


def callback(ch, method, properties, body):

    data = json.loads(body.decode())

    print("[PMS] Command received:", data)
    print("[PMS] Routing key:", method.routing_key)
    try:

        if method.routing_key == "cmd.pms.confirmar-reserva":
            handle_confirm_reservation(data)

        elif method.routing_key == "cmd.pms.cancelar-reserva":
            handle_cancel_reservation(data)

        else:
            print("Comando no reconocido")

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
        routing_key=ROUTING_KEY_CONFIRM
    )

    channel.queue_bind(
        exchange=COMMANDS_EXCHANGE,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY_CANCEL
    )

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )

    print("Listening on queue:", QUEUE_NAME)

    channel.start_consuming()