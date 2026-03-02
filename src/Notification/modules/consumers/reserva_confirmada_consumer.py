
import json
import pika
from config.rabbitmq import create_connection
from modules.services.email_service import send_voucher_email
from modules.publishers.voucher_enviado_publisher import publish_voucher_enviado

def callback(ch, method, properties, body):
    print("Evento recibido")
    print(body)
    
    data = json.loads(body)
    
    reserva_id = data.get("reservaId")
    email = data.get("emailCliente")

    send_voucher_email(email, reserva_id)
    publish_voucher_enviado(reserva_id)

    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    
    print("Notification service started")
    print("Waiting for ReservaConfirmadaEvt...")

    connection = create_connection()
    channel = connection.channel()

    channel.queue_declare(
        queue="booking.reserva.confirmada",
        durable=True
    )

    channel.basic_consume(
        queue="booking.reserva.confirmada",
        on_message_callback=callback,
        auto_ack=False
    )

    print("Waiting for events...")
    channel.start_consuming()
