
import json
import pika
from config.settings import settings

def publish_voucher_enviado(reserva_id: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue="notification.voucher.enviado")
    
    event = {
        "eventType": "VoucherEnviadoEvt",
        "reservaId": reserva_id,
        "status": "ENVIADO"
    }
    
    channel.basic_publish(
        exchange="",
        routing_key="notification.voucher.enviado",
        body=json.dumps(event)
    )
    
    connection.close()
