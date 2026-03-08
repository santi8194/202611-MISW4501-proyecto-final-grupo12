
import json
import pika
from config.rabbitmq import create_connection
from modules.services.email_service import send_voucher_email
from modules.publishers.voucher_enviado_publisher import publish_voucher_enviado

EVENTS_EXCHANGE = "travelhub.events.exchange"
QUEUE_NAME = "notification.events.queue"
ROUTING_KEY = "evt.reserva.confirmada"

def callback(ch, method, properties, body):
    try:
        print("Evento recibido:", body)

        data = json.loads(body.decode())

        event_type = data.get("type")

        if event_type != "ReservaConfirmadaEvt":
            print("Evento ignorado:", event_type)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        payload = data.get("data", data)
        reserva_id = payload.get("id_reserva")
        email = payload.get("emailCliente")

        print(f"Procesando reserva {reserva_id} para {email}")

        send_voucher_email(email, reserva_id)
        publish_voucher_enviado(reserva_id)

        ch.basic_ack(delivery_tag=method.delivery_tag)

        print(f"Evento recibido y procesado: {event_type} para reserva {reserva_id}", flush=True)

    except Exception as e:
        print("Error procesando evento:", e)

def start_consumer():

    print("Notification service started")
    print("Waiting for evt.reserva.confirmada...")

    connection = create_connection()
    channel = connection.channel()

    # Declarar exchange de eventos
    channel.exchange_declare(
        exchange=EVENTS_EXCHANGE,
        exchange_type="topic",
        durable=True
    )

    # Declarar cola del servicio
    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    # Vincular cola al exchange
    channel.queue_bind(
        exchange=EVENTS_EXCHANGE,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY
    )

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=False
    )

    print("Waiting for events...")
    channel.start_consuming()