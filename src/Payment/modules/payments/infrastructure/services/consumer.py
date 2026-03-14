import json
from config.rabbitmq import create_connection
from modules.payments.infrastructure.services.handlers import handle_process_payment, handle_refund_payment

COMMANDS_EXCHANGE = "travelhub.commands.exchange"
QUEUE_NAME = "payment.commands.queue"
ROUTING_KEY_PROCESS_PAYMENT = "cmd.payment.procesar-pago"
ROUTING_KEY_REVERT_PAYMENT = "cmd.payment.reversar-pago"


def callback(ch, method, properties, body):
    
    data = json.loads(body.decode())

    print("[PAYMENTS] Command received:", data)
    print("[PAYMENTS] Routing key:", method.routing_key)

    try:

        if method.routing_key == ROUTING_KEY_PROCESS_PAYMENT:
            handle_process_payment(data)

        elif method.routing_key == ROUTING_KEY_REVERT_PAYMENT:
            handle_refund_payment(data)
        else:
            print("[PAYMENTS] Command not recognized")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:

        print("[PAYMENTS] Error processing command:", e)

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
        routing_key=ROUTING_KEY_PROCESS_PAYMENT
    )

    channel.queue_bind(
        exchange=COMMANDS_EXCHANGE,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY_REVERT_PAYMENT
    )

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )

    print("Listening on queue:", QUEUE_NAME)
    channel.start_consuming()