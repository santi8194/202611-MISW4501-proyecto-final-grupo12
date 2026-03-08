import json
import pika
from config.settings import settings

EVENTS_EXCHANGE = "travelhub.events.exchange"
ROUTING_KEY = "evt.voucher.enviado"

def publish_voucher_enviado(reserva_id: str):

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=settings.RABBITMQ_HOST)
    )

    channel = connection.channel()

    # Declarar exchange de eventos
    channel.exchange_declare(
        exchange=EVENTS_EXCHANGE,
        exchange_type="topic",
        durable=True
    )

    event = {
        "type": "VoucherEnviadoEvt",
        "id_reserva": reserva_id,
        "status": "ENVIADO"
    }

    channel.basic_publish(
        exchange=EVENTS_EXCHANGE,
        routing_key=ROUTING_KEY,
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    print(f"Evento publicado: {ROUTING_KEY} para reserva {reserva_id}", flush=True)

    connection.close()