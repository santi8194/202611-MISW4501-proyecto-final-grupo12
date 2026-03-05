import pika
import json
import os
from dataclasses import asdict
from Booking.modulos.reserva.infraestructura.mapeadores import MapeadorEventosReserva
from Booking.seedwork.aplicacion.dispatchers import Despachador

class DespachadorRabbitMQ(Despachador):

    def __init__(self):
        self._mapeador = MapeadorEventosReserva()
        # En un ambiente real, la URL de conexión vendría de variables de entorno
        # host = os.getenv('RABBITMQ_HOST', 'localhost') # This line is commented out as connection is now per-message
        # self.conexion = pika.BlockingConnection(pika.ConnectionParameters(host)) # This line is commented out as connection is now per-message
        # self.canal = self.conexion.channel() # This line is commented out as connection is now per-message

        # Aseguramos que el exchange existe. Usamos 'topic' para que los servicios
        # se puedan suscribir a flujos de eventos específicos con routing keys.
        # self.canal.exchange_declare(exchange='eventos_dominio', exchange_type='topic', durable=True) # This line is commented out as connection is now per-message
        # self.canal.exchange_declare(exchange='comandos_saga', exchange_type='direct', durable=True) # This line is commented out as connection is now per-message

    def _publicar_mensaje(self, payload_dict, topico, tipo_evento):
        try:
            # Obtenemos el host y port de variables de entorno
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
            rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
            channel = connection.channel()
            channel.exchange_declare(exchange=topico, exchange_type='fanout')
            
            # Formateamos el payload en JSON puro (Equivalente al Avro de Pulsar)
            mensaje = json.dumps(payload_dict)
            
            channel.basic_publish(
                exchange=topico,
                routing_key='',
                body=mensaje,
                properties=pika.BasicProperties(
                    content_type='application/json',
                    type=tipo_evento
                )
            )
            print(f"[RabbitMQ] Evento Integración Publicado en '{topico}': {tipo_evento}")
            connection.close()
        except Exception as e:
            print(f"[RabbitMQ] Error publicando evento: {e}")

    def publicar_evento(self, evento, topico):
        # 1. El Despachador toma el Evento de Dominio puro (ej. ReservaPendiente)
        # 2. Usa el Mapeador para traducirlo al DTO de Integración
        evento_integracion = self._mapeador.entidad_a_dto(evento)
        
        if evento_integracion:
            # 3. Lo publica usando el diccionario nativo del payload
            self._publicar_mensaje(evento_integracion.to_dict(), topico, evento_integracion.type)
        else:
            print(f"[RabbitMQ] Evento de dominio {evento.__class__.__name__} fue ignorado (No tiene mapeo a Integración)")

    def publicar_comando(self, comando, routing_key: str):
        payload = json.dumps(asdict(comando), default=str)
        try:
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
            rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
            channel = connection.channel()
            channel.exchange_declare(exchange='comandos_saga', exchange_type='direct')
            channel.basic_publish(
                exchange='comandos_saga',
                routing_key=routing_key,
                body=payload,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            print(f"[RabbitMQ] Comando despachado: {routing_key} -> {payload}")
            connection.close()
        except Exception as e:
            print(f"[RabbitMQ] Error publicando comando: {e}")

    def cerrar(self):
        # La conexión se cierra por mensaje, por lo que no hay una conexión persistente para cerrar aquí.
        # Si se reintroduce una conexión persistente, esta lógica debería ser restaurada.
        pass
