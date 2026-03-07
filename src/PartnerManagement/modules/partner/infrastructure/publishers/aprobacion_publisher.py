import json
import pika
from config.rabbitmq import create_connection

# Nombre del exchange (intercambiador) donde publicaremos los eventos.
EVENTS_EXCHANGE = "travelhub.events.exchange"

def publish_event(routing_key: str, event_type: str, data: dict):
    """
    Función genérica para publicar un evento en RabbitMQ.
    :param routing_key: La clave de enrutamiento que define a qué colas irá el mensaje.
    :param event_type: El tipo de evento (ej. ReservaAprobadaManualEvt).
    :param data: Un diccionario con los datos del evento (payload).
    """
    connection = None
    try:
        connection = create_connection()
        channel = connection.channel()

        # Regla 1: Usar exchange de eventos como 'topic'
        # Regla 4: No crear ni bindear colas desde el publicador, solo usar el exchange
        channel.exchange_declare(
            exchange=EVENTS_EXCHANGE,
            exchange_type="topic",
            durable=True
        )

        message = {
            "type": event_type,
            **data
        }

        channel.basic_publish(
            exchange=EVENTS_EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hacer que el mensaje sea persistente
            )
        )
        print(f"[{event_type}] Publicado a {routing_key} sobre {EVENTS_EXCHANGE}")
    except Exception as e:
        print(f"Error publicando evento {event_type}:", e)
    finally:
        if connection and connection.is_open:
            connection.close()

def publish_reserva_aprobada(id_reserva: str):
    """
    Publica el evento de éxito indicando que la reserva fue aprobada.
    """
    publish_event(
        # Regla 2: Formato de eventos: evt.<dominio>.<resultado>
        routing_key="evt.partnermanagement.reserva-aprobada",
        event_type="ReservaAprobadaManualEvt",
        data={"id_reserva": id_reserva}
    )

def publish_reserva_rechazada(id_reserva: str, motivo: str):
    """
    Publica el evento de fallo indicando que la reserva fue rechazada.
    """
    publish_event(
        # Regla 2: Formato de eventos: evt.<dominio>.<resultado>
        routing_key="evt.partnermanagement.reserva-rechazada",
        event_type="ReservaRechazadaManualEvt",
        data={"id_reserva": id_reserva, "motivo": motivo}
    )
