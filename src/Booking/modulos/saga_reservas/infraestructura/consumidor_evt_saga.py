import pika
import json
import os
import sys
# Agregar el directorio Booking al path para poder importar módulos propios en ejecución standalone
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import argparse
import uuid
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importar contexto de base de datos y orquestador
from Booking.config.db import db
from Booking.modulos.saga_reservas.aplicacion.orquestador import OrquestadorSagaReservas
from Booking.modulos.saga_reservas.infraestructura.repositorios import RepositorioSagas
from Booking.config.uow import UnidadTrabajoHibrida

def get_db_session():
    # Obtienemos la sesión de BD de SQLAlchemy configurada
    # Ya que corremos fuera de Flask de forma aislada
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME')

    if all([db_user, db_password, db_host, db_name]):
        connection_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    else:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'database', 'booking.db'))
        # connection_url = f'sqlite:///{db_path}'
        connection_url = "sqlite:///:memory:"
        
    engine = create_engine(connection_url)
    Session = sessionmaker(bind=engine)
    return Session()

def procesar_mensaje(ch, method, properties, body):
    try:
        mensaje = json.loads(body)
        print(f"\n[SAGA WORKER] Mensaje Recibido: {method.routing_key}")
        
        from Booking.api import create_app
        print("[SAGA WORKER] Creando Flask App en memoria...", flush=True)
        app = create_app()
        
        with app.app_context():
            print("[SAGA WORKER] Entró al app context", flush=True)
            repo_sagas = RepositorioSagas() # Usa db.session por defecto
            uow = UnidadTrabajoHibrida()
            print("[SAGA WORKER] UoW inicializado", flush=True)
            orquestador = OrquestadorSagaReservas(repositorio=repo_sagas, uow=uow)

            # Validar tipo de evento esperado (por convención o por key)
            if method.routing_key == "evt.reserva.creada":
                
                # Extraer payload base
                payload = mensaje.get('data', {})
                id_reserva = payload.get('id_reserva') or mensaje.get('id_reserva')
                id_usuario = payload.get('id_usuario') or payload.get('id_cliente') or mensaje.get('id_usuario', str(uuid.uuid4()))
                monto = payload.get('monto') or mensaje.get('monto', 1500.0)
                id_habitacion = payload.get('id_habitacion') or mensaje.get('id_habitacion')
                fecha_reserva = payload.get('fecha_reserva') or mensaje.get('fecha_reserva')
                
                if not id_reserva:
                     print("[SAGA WORKER] Ignorando evento: id_reserva vacío")
                     ch.basic_ack(delivery_tag=method.delivery_tag)
                     return

                print(f"[SAGA WORKER] Iniciando Saga para reserva: {id_reserva} (Fecha: {fecha_reserva})")
                     
                print(f"[SAGA WORKER] Llamando orquestador con id_reserva: {id_reserva}", flush=True)
                res = orquestador.iniciar_saga(
                    id_reserva=uuid.UUID(str(id_reserva)),
                    id_usuario=uuid.UUID(str(id_usuario)),
                    monto=float(monto),
                    id_habitacion=uuid.UUID(str(id_habitacion)) if id_habitacion else None,
                    fecha_reserva=fecha_reserva
                )
                print(f"[SAGA WORKER] Orquestador terminó con resultado: {res}", flush=True)
                     
            else:
                # Es un evento de respuesta de otro microservicio
                payload = mensaje.get('data', {}) or mensaje
                id_reserva = payload.get('id_reserva') or mensaje.get('id_reserva')
                
                if not id_reserva:
                    print(f"[SAGA WORKER] Ignorando evento {method.routing_key}: No contiene id_reserva")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                data = json.loads(body.decode())
                evento_tipo = data["type"] if "type" in data else method.routing_key
                print(f"[SAGA WORKER] Procesando evento de respuesta {evento_tipo} para reserva: {id_reserva}")
                
                # Pasar al orquestador
                orquestador.manejar_evento_respuesta(
                    id_reserva=uuid.UUID(str(id_reserva)),
                    evento_recibido=evento_tipo,
                    payload_recibido=payload
                )

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print("[SAGA WORKER] Mensaje procesado y Acknowledge enviado.")
        
    except Exception as e:
        print(f"[SAGA WORKER] Error procesando mensaje {method.routing_key}: {e}")
        # Rechazamos el mensaje sin requeue en caso de error fatal de sintaxis
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def iniciar_consumidor():
    print("[SAGA WORKER] Iniciando consumidor de RabbitMQ...")
    
    # Intentar conexión con retries de forma resiliente
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    
    connection = None
    retries = 5
    while retries > 0:
         try:
             connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
             break
         except pika.exceptions.AMQPConnectionError:
             print(f"[SAGA WORKER] RabbitMQ no disponible ({rabbitmq_host}:{rabbitmq_port}), reintentando...")
             retries -= 1
             time.sleep(3)

    if not connection:
         print("[SAGA WORKER] Fatal: No se pudo conectar a RabbitMQ.")
         sys.exit(1)

    channel = connection.channel()

    # Rule 1 & 4 (Consumers): Consumer declara exchange si quiere garantizar que existe (opcional)
    # pero obligatoriamente crea su propia COLA y hace sus propios BINDINGS
    
    exchange_name = 'travelhub.events.exchange'
    queue_name = 'saga_reservas.events.queue'
    # Escuchar todos los eventos para la saga
    routing_key = 'evt.#'
    
    # Declaramos el exchange como topic
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic', durable=True)
    
    # Declaramos la cola propia del worker
    channel.queue_declare(queue=queue_name, durable=True)
    
    # Bindeamos la cola al exchange con los Topics que nos interesan
    channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
    
    # Quality of Service
    channel.basic_qos(prefetch_count=1)
    
    # Suscribirse
    channel.basic_consume(queue=queue_name, on_message_callback=procesar_mensaje)

    print(f" [*] SAGA WORKER esperando eventos ('{routing_key}') en la cola '{queue_name}'. Para salir presione CTRL+C", flush=True)
    channel.start_consuming()

if __name__ == '__main__':
    try:
        # Forcing unbuffered stdout for Docker logs
        sys.stdout.reconfigure(line_buffering=True)
        iniciar_consumidor()
    except KeyboardInterrupt:
        print('Worker detenido manualmente.', flush=True)
