import pika
import json
import os
from dataclasses import asdict
from Booking.seedwork.aplicacion.dispatchers import Despachador

class DespachadorRabbitMQ(Despachador):

    def __init__(self, mapeador_eventos=None):
        self._mapeador = mapeador_eventos
        # En un ambiente real, la URL de conexión vendría de variables de entorno
        # host = os.getenv('RABBITMQ_HOST', 'localhost') # This line is commented out as connection is now per-message
        # self.conexion = pika.BlockingConnection(pika.ConnectionParameters(host)) # This line is commented out as connection is now per-message
        # self.canal = self.conexion.channel() # This line is commented out as connection is now per-message

        # Aseguramos que el exchange existe. Usamos 'topic' para que los servicios
        # se puedan suscribir a flujos de eventos específicos con routing keys.
        # self.canal.exchange_declare(exchange='eventos_dominio', exchange_type='topic', durable=True) # This line is commented out as connection is now per-message
        # self.canal.exchange_declare(exchange='comandos_saga', exchange_type='direct', durable=True) # This line is commented out as connection is now per-message

    def _publicar_mensaje(self, payload_dict, topico_exchange, tipo_evento, routing_key):
        try:
            # Obtenemos el host y port de variables de entorno
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
            rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
            channel = connection.channel()
            # Rule 4: Publishers don't create queues. We also assume exchanges are created by infra/consumers.
            # channel.exchange_declare(exchange=topico, exchange_type='fanout')
            
            # Formateamos el payload en JSON puro (Equivalente al Avro de Pulsar)
            mensaje = json.dumps(payload_dict)
            
            channel.basic_publish(
                exchange=topico_exchange,
                routing_key=routing_key,
                body=mensaje,
                properties=pika.BasicProperties(
                    content_type='application/json',
                    type=tipo_evento
                )
            )
            print(f"[RabbitMQ] Evento/Comando Publicado en '{topico_exchange}' con routing key '{routing_key}': {tipo_evento}")
            connection.close()
        except Exception as e:
            print(f"[RabbitMQ] Error publicando mensaje: {e}")

    def publicar_evento(self, evento, topico=""): 
        # El parámetro topico de la interfaz original ahora se ignora en pro del enrutamiento dinámico
        
        # Hack para comandos que fueron pasados como eventos
        tipo = getattr(evento, '__class__').__name__
        if "Cmd" in tipo or "EsperandoVoucher" in tipo:
            exchange = "travelhub.commands.exchange"
            routing_key = ""
            if tipo == "ProcesarPagoCmd":
                routing_key = "cmd.payment.procesar-pago"
            elif tipo == "ConfirmarReservaPmsCmd":
                routing_key = "cmd.pms.confirmar-reserva"
            elif tipo == "SolicitarAprobacionManualCmd":
                routing_key = "cmd.partnermanagement.solicitar-aprobacion"
            elif tipo == "ReversarPagoCmd":
                routing_key = "cmd.payment.reversar-pago"
            elif tipo == "CancelarReservaPmsCmd":
                routing_key = "cmd.pms.cancelar-reserva"
            import uuid
            class UUIDEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, uuid.UUID):
                        return str(obj)
                    return json.JSONEncoder.default(self, obj)

            if hasattr(evento, '__dataclass_fields__'):
                payload_str = json.dumps(asdict(evento), cls=UUIDEncoder)
                payload = json.loads(payload_str)
            else:
                payload = json.loads(json.dumps(evento, cls=UUIDEncoder))
                
            print(f"[RabbitMQ] Publicando CMD mapeado directo: {tipo}")
            self._publicar_mensaje(payload, exchange, tipo, routing_key)
            return

        evento_integracion = self._mapeador.entidad_a_dto(evento)
        
        if evento_integracion:
            tipo = evento_integracion.type
            exchange = ""
            routing_key = ""
            
            # Eventos
            if "Evt" in tipo or tipo == "ReservaPendiente":
                exchange = "travelhub.events.exchange"
                if tipo == "ReservaCreadaIntegracionEvt":
                    routing_key = "evt.reserva.creada"
                elif tipo == "ReservaPendiente":
                    routing_key = "evt.reserva.pendiente"
                elif tipo == "PagoExitosoEvt":
                    routing_key = "evt.pago.exitoso"
                elif tipo == "PagoRechazadoEvt":
                    routing_key = "evt.pago.rechazado"
                elif tipo == "ConfirmacionPmsExitosaEvt":
                    routing_key = "evt.pms.confirmacion_exitosa"
                elif tipo == "ReservaRechazadaPmsEvt":
                    routing_key = "evt.pms.rechazada"
                elif tipo == "ReservaAprobadaManualEvt":
                    routing_key = "evt.partnermanagement.aprobada"
                elif tipo == "ReservaRechazadaManualEvt":
                    routing_key = "evt.partnermanagement.rechazada"
                elif tipo == "ReservaConfirmadaEvt":
                    routing_key = "evt.reserva.confirmada"
                elif tipo == "VoucherEnviadoEvt":
                    routing_key = "evt.voucher.enviado"
                elif tipo == "FalloEnvioVoucherEvt":
                    routing_key = "evt.notification.fallo_envio"
                else: 
                     routing_key = f"evt.generico.{tipo.lower()}"
                     print(f"[RabbitMQ] Advertencia: Tipo de evento '{tipo}' no mapeado formalmente. Usando '{routing_key}'")

            # Comandos
            elif "Cmd" in tipo or "EsperandoVoucher" in tipo:
                exchange = "travelhub.commands.exchange"
                if tipo == "ProcesarPagoCmd":
                    routing_key = "cmd.payment.procesar-pago"
                elif tipo == "ConfirmarReservaPmsCmd":
                    routing_key = "cmd.pms.confirmar-reserva"
                elif tipo == "SolicitarAprobacionManualCmd":
                    routing_key = "cmd.partnermanagement.solicitar-aprobacion"
                elif tipo == "ReversarPagoCmd":
                    routing_key = "cmd.payment.reversar-pago"
                elif tipo == "CancelarReservaPmsCmd":
                    routing_key = "cmd.pms.cancelar-reserva"
                # Comandos locales del Booking no deberían ir a rmq, pero si llegan por UOW...
                elif "LocalCmd" in tipo: 
                     routing_key = f"cmd.booking.{tipo.lower()}"
                else:
                    routing_key = f"cmd.generico.{tipo.lower()}"
                    print(f"[RabbitMQ] Advertencia: Tipo de comando '{tipo}' no mapeado formalmente. Usando '{routing_key}'")
            
            if exchange and routing_key:
                self._publicar_mensaje(evento_integracion.to_dict(), exchange, tipo, routing_key)
            else:
                 print(f"[RabbitMQ] No se pudo determinar el routing para {tipo}")
        else:
            print(f"[RabbitMQ] Evento de dominio {evento.__class__.__name__} fue ignorado (No tiene mapeo a Integración)")

    def publicar_comando(self, comando, routing_key: str):
        # We enforce the new exchange here, although the routing_key is provided externally
        # Ideally, this should also map or use the provided routing key directly.
        payload = json.dumps(asdict(comando), default=str)
        try:
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
            rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
            channel = connection.channel()
            # Rule 4: Publishers don't create queues or exchanges implicitly, assume it exists
            # channel.exchange_declare(exchange='comandos_saga', exchange_type='direct')
            
            # Use the new centralized command exchange
            exchange = "travelhub.commands.exchange"
            
            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=payload,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            print(f"[RabbitMQ] Comando despachado directo a '{exchange}': {routing_key}")
            connection.close()
        except Exception as e:
            print(f"[RabbitMQ] Error publicando comando directo: {e}")

    def cerrar(self):
        # La conexión se cierra por mensaje, por lo que no hay una conexión persistente para cerrar aquí.
        # Si se reintroduce una conexión persistente, esta lógica debería ser restaurada.
        pass
