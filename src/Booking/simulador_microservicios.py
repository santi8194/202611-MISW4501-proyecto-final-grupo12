import argparse
import json
import logging
import os
import sys
import time
import uuid

import pika

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))

COMMANDS_EXCHANGE = 'travelhub.commands.exchange'
EVENTS_EXCHANGE = 'travelhub.events.exchange'

class SimuladorMicroservicios:
    def __init__(self, modo):
        self.modo = modo
        self.connection = None
        self.channel = None
        self.habitaciones_confirmadas = set() # Simula el inventario concurrente
        
    def conectar(self):
        retries = 5
        while retries > 0:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
                self.channel = self.connection.channel()
                logger.info("Conectado a RabbitMQ.")
                break
            except pika.exceptions.AMQPConnectionError:
                logger.warning(f"RabbitMQ no disponible en {RABBITMQ_HOST}:{RABBITMQ_PORT}. Reintentando...")
                retries -= 1
                time.sleep(3)
        
        if not self.connection:
            logger.error("No se pudo conectar a RabbitMQ.")
            sys.exit(1)

        # Declarar exchanges (normalmente infra, pero por seguridad)
        self.channel.exchange_declare(exchange=COMMANDS_EXCHANGE, exchange_type='direct', durable=True)
        self.channel.exchange_declare(exchange=EVENTS_EXCHANGE, exchange_type='topic', durable=True)
        
    def configurar_consumidores(self):
        # Mapeo de Colas a Routing Keys que deben escuchar
        colas_routing = {
            'payment.commands.queue': ['cmd.payment.procesar-pago', 'cmd.payment.reversar-pago'],
            'pms.commands.queue': ['cmd.pms.confirmar-reserva', 'cmd.pms.cancelar-reserva'],
            'partnermanagement.commands.queue': ['cmd.partnermanagement.solicitar-aprobacion'],
            # Notification escucha Eventos, no Comandos
            'notification.events.queue': ['evt.reserva.confirmada']
        }
        
        for cola, routing_keys in colas_routing.items():
            self.channel.queue_declare(queue=cola, durable=True)
            
            # Determinar a qué exchange bindear la cola basado en el prefijo 
            # de la primera routing key (para saber si es cmd o evt)
            exchange = EVENTS_EXCHANGE if routing_keys[0].startswith('evt.') else COMMANDS_EXCHANGE
            
            for key in routing_keys:
                self.channel.queue_bind(exchange=exchange, queue=cola, routing_key=key)
                
            # Configurar el consumo
            self.channel.basic_consume(queue=cola, on_message_callback=self.procesar_mensaje)
            logger.info(f"Escuchando en la cola '{cola}' para las keys: {routing_keys}")

    def publicar_evento(self, evento_tipo, routing_key, payload):
        mensaje = json.dumps(payload)
        self.channel.basic_publish(
            exchange=EVENTS_EXCHANGE,
            routing_key=routing_key,
            body=mensaje,
            properties=pika.BasicProperties(
                content_type='application/json',
                type=evento_tipo
            )
        )
        logger.info(f"Evento publicado: {routing_key} ({evento_tipo})")

    def procesar_mensaje(self, ch, method, properties, body):
        try:
            mensaje = json.loads(body)
            routing_key = method.routing_key
            logger.info(f"Mensaje recibido: {routing_key}")
            
            # Extraer id_reserva (puede venir en payload.data o directo)
            payload_db = mensaje.get('data', mensaje)
            id_reserva = payload_db.get('id_reserva')
            
            if not id_reserva:
                logger.warning(f"Mensaje sin id_reserva ignorado: {routing_key}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Simular tiempo de procesamiento
            time.sleep(1)

            # --- PAYMENT ---
            if routing_key == "cmd.payment.procesar-pago":
                logger.info(f"Simulando Procesar Pago para reserva {id_reserva}...")
                self.publicar_evento(
                    "PagoExitosoEvt", 
                    "evt.pago.exitoso", 
                    {"id_reserva": id_reserva, "token_pasarela": f"token_{uuid.uuid4().hex[:6]}"}
                )
                
            elif routing_key == "cmd.payment.reversar-pago":
                logger.info(f"[COMPENSACIÓN] Simulando Reversar Pago para reserva {id_reserva}")
                
            # --- PMS ---
            elif routing_key == "cmd.pms.confirmar-reserva":
                logger.info(f"Simulando Confirmar Reserva PMS para reserva {id_reserva}...")
                
                # Caso 3: Idempotencia y control de concurrencia de habitación
                id_habitacion = payload_db.get('id_habitacion')
                if id_habitacion and id_habitacion in self.habitaciones_confirmadas:
                    logger.warning(f"❌ PMS Rechaza: La habitación {id_habitacion} ya está confirmada por otra reserva.")
                    self.publicar_evento(
                        "ReservaRechazadaPmsEvt", 
                        "evt.pms.rechazado", 
                        {"id_reserva": id_reserva, "motivo": "Habitación sin cupo"}
                    )
                else:
                    if id_habitacion:
                        self.habitaciones_confirmadas.add(id_habitacion)
                    
                    self.publicar_evento(
                        "ConfirmacionPmsExitosaEvt", 
                        "evt.pms.confirmacion_exitosa", 
                        {"id_reserva": id_reserva, "codigo_pms": f"HTL-{uuid.uuid4().hex[:4].upper()}"}
                    )
                
            elif routing_key == "cmd.pms.cancelar-reserva":
                logger.info(f"[COMPENSACIÓN] Simulando Cancelar Reserva PMS para reserva {id_reserva}")
                id_habitacion = payload_db.get('id_habitacion')
                if id_habitacion and id_habitacion in self.habitaciones_confirmadas:
                    self.habitaciones_confirmadas.remove(id_habitacion)
                    logger.info(f"✅ PMS libera habitación {id_habitacion}")

            elif routing_key == "cmd.partnermanagement.solicitar-aprobacion":
                logger.info(f"Simulando Aprobacion Manual ({self.modo}) para reserva {id_reserva}...")
                if self.modo == 'exito':
                    self.publicar_evento(
                        "ReservaAprobadaManualEvt", 
                        "evt.partnermanagement.aprobada", 
                        {"id_reserva": id_reserva, "status": "aprobado"}
                    )
                else:
                    self.publicar_evento(
                        "ReservaRechazadaManualEvt", 
                        "evt.partnermanagement.rechazada", 
                        {"id_reserva": id_reserva, "motivo": "Rechazado manualmente"}
                    )

            # --- NOTIFICATION ---
            elif routing_key == "evt.reserva.confirmada":
                 logger.info(f"Simulando Envio de Voucher por Coreografia para reserva {id_reserva}...")
                 self.publicar_evento(
                    "VoucherEnviadoEvt", 
                    "evt.voucher.enviado", 
                    {"id_reserva": id_reserva, "email": "cliente-simulado@dummy.com"}
                 )

            else:
                 logger.warning(f"Comando no manejado por el simulador: {routing_key}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def iniciar(self):
        self.conectar()
        self.configurar_consumidores()
        logger.info(f"=== SIMULADOR DE MICROSERVICIOS INICIADO (Modo: {self.modo.upper()}) ===")
        logger.info("Esperando comandos en RabbitMQ. Presiona CTRL+C para salir.")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Simulador detenido por el usuario.")
            if self.connection and self.connection.is_open:
                self.connection.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulador de microservicios para la saga de Booking')
    parser.add_argument('--modo', choices=['exito', 'fallo'], default='exito', help='Modo de simulación (exito/fallo)')
    args = parser.parse_args()
    
    # Forzar salida no bufferizada
    sys.stdout.reconfigure(line_buffering=True)
    
    simulador = SimuladorMicroservicios(args.modo)
    simulador.iniciar()
