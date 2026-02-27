import pika
import os
import json
from dataclasses import asdict

class DespachadorRabbitMQ:
    def __init__(self):
        # En un ambiente real, la URL de conexión vendría de variables de entorno
        host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.conexion = pika.BlockingConnection(pika.ConnectionParameters(host))
        self.canal = self.conexion.channel()

        # Aseguramos que el exchange existe. Usamos 'topic' para que los servicios
        # se puedan suscribir a flujos de eventos específicos con routing keys.
        self.canal.exchange_declare(exchange='eventos_dominio', exchange_type='topic', durable=True)
        self.canal.exchange_declare(exchange='comandos_saga', exchange_type='direct', durable=True)

    def publicar_evento(self, evento, routing_key: str):
        payload = json.dumps(asdict(evento), default=str)
        self.canal.basic_publish(
            exchange='eventos_dominio',
            routing_key=routing_key,
            body=payload,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hacer el mensaje persistente
            )
        )
        print(f"[RabbitMQ] Evento despachado: {routing_key} -> {payload}")

    def publicar_comando(self, comando, routing_key: str):
        payload = json.dumps(asdict(comando), default=str)
        self.canal.basic_publish(
            exchange='comandos_saga',
            routing_key=routing_key,
            body=payload,
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        print(f"[RabbitMQ] Comando despachado: {routing_key} -> {payload}")

    def cerrar(self):
        if self.conexion and not self.conexion.is_closed:
            self.conexion.close()
