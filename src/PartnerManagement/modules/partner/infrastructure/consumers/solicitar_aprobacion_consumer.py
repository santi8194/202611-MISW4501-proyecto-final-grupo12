import json
import random
from config.rabbitmq import create_connection
from modules.partner.infrastructure.publishers.aprobacion_publisher import (
    publish_reserva_aprobada,
    publish_reserva_rechazada
)

# Constantes de configuración para RabbitMQ
COMMANDS_EXCHANGE = "travelhub.commands.exchange" # Regla 1: Exchange separado para comandos (direct)
QUEUE_NAME = "partnermanagement.commands.queue" # Regla 3: Cola con nombre específico del servicio '<servicio>.commands.queue'
ROUTING_KEY = "cmd.partnermanagement.solicitar-aprobacion" # Regla 2: Llave de ruteo como 'cmd.servicio.accion'

def callback(ch, method, properties, body):
    """
    Función que se ejecuta cada vez que llega un mensaje a la cola 'partnermanagement.commands.queue'.
    """
    try:
        data = json.loads(body.decode())
        command_type = data.get("commandType", data.get("type", ""))
        ##imprimir command_type 
        print("data data:", data)
        print("Comando ignorado:", command_type)
        #if command_type not in ["SolicitarAprobacionManualCmd", "SolicitarAprobacionManual"]:
        #    print("Comando ignorado:", command_type)
        #    ch.basic_ack(delivery_tag=method.delivery_tag)
        #    return

        id_reserva = data.get("id_reserva")
        if not id_reserva:
            id_reserva = data.get("reservaId") 

        print(f"Recibido Comando {command_type} vía {ROUTING_KEY} para la reserva: {id_reserva}")

        if random.random() < 0.8:
            print(f"Aprobando manualmente la reserva {id_reserva}")
            publish_reserva_aprobada(id_reserva)
        else:
            print(f"Rechazando manualmente la reserva {id_reserva} por reporte negativo")
            publish_reserva_rechazada(id_reserva, "El cliente está reportado negativamente")

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print("Error procesando comando:", e)

def start_consumer():
    """
    Función para inicializar el consumidor e iniciar la escucha activa de mensajes.
    """
    print("PartnerManagement Consumer Service started")
    print(f"Waiting for {ROUTING_KEY} on {COMMANDS_EXCHANGE}...")

    connection = create_connection()
    channel = connection.channel()

    # Regla 1: Declarar el exchange de comandos para asegurarnos de que ya exista y sea 'direct'
    channel.exchange_declare(
        exchange=COMMANDS_EXCHANGE,
        exchange_type="direct",
        durable=True
    )

    # Regla 3 y 4: Definimos nuestra cola exclusiva
    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True
    )

    # Regla 2: Vinculamos al exchange "direct" con nuestra llave "cmd.partnermanagement.aprobacion-manual"
    channel.queue_bind(
        exchange=COMMANDS_EXCHANGE,
        queue=QUEUE_NAME,
        routing_key=ROUTING_KEY
    )

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=False
    )

    print("Listening on queue: " + QUEUE_NAME)
    channel.start_consuming()
