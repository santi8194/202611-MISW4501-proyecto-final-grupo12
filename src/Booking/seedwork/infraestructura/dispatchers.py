import logging
import pika
import json
import os
from dataclasses import asdict
from Booking.seedwork.aplicacion.dispatchers import Despachador

logger = logging.getLogger(__name__)


class DespachadorRabbitMQ(Despachador):
    """
    Publica eventos y comandos hacia RabbitMQ.
    
    Estrategia de conexión (R10):
    La conexión se abre de forma lazy en el primer mensaje del ciclo de vida
    del despachador y se reutiliza para todos los mensajes del mismo ciclo
    (habitualmente un commit de UoW). Se cierra explícitamente al llamar cerrar().
    Esto evita el overhead de abrir/cerrar un socket TCP por cada evento.
    """

    def __init__(self, mapeador_eventos=None):
        self._mapeador = mapeador_eventos
        self._connection: pika.BlockingConnection | None = None
        self._channel = None

    # ------------------------------------------------------------------
    # Gestión de conexión
    # ------------------------------------------------------------------

    def _get_channel(self):
        """Devuelve el canal activo, creando la conexión si no existe."""
        if not self._connection or self._connection.is_closed:
            rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
            rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)
            )
            self._channel = self._connection.channel()
            logger.info(f"[RabbitMQ] Conexión abierta a {rabbitmq_host}:{rabbitmq_port}")
        return self._channel

    def cerrar(self):
        """Cierra la conexión al finalizar el ciclo de la UoW."""
        if self._connection and self._connection.is_open:
            try:
                self._connection.close()
                logger.info("[RabbitMQ] Conexión cerrada correctamente.")
            except Exception as e:
                logger.warning(f"[RabbitMQ] Error al cerrar conexión: {e}")
        self._connection = None
        self._channel = None

    # ------------------------------------------------------------------
    # Routing Registry
    # ------------------------------------------------------------------

    ROUTING_REGISTRY = {
        # Comandos
        "ProcesarPagoCmd": ("travelhub.commands.exchange", "cmd.payment.procesar-pago"),
        "ConfirmarReservaPmsCmd": ("travelhub.commands.exchange", "cmd.pms.confirmar-reserva"),
        "SolicitarAprobacionManualCmd": ("travelhub.commands.exchange", "cmd.partnermanagement.solicitar-aprobacion"),
        "ReversarPagoCmd": ("travelhub.commands.exchange", "cmd.payment.reversar-pago"),
        "CancelarReservaPmsCmd": ("travelhub.commands.exchange", "cmd.pms.cancelar-reserva"),

        # Eventos
        "ReservaCreadaIntegracionEvt": ("travelhub.events.exchange", "evt.reserva.creada"),
        "ReservaPendiente": ("travelhub.events.exchange", "evt.reserva.pendiente"),
        "PagoExitosoEvt": ("travelhub.events.exchange", "evt.pago.exitoso"),
        "PagoRechazadoEvt": ("travelhub.events.exchange", "evt.pago.rechazado"),
        "ConfirmacionPmsExitosaEvt": ("travelhub.events.exchange", "evt.pms.confirmacion_exitosa"),
        "ReservaRechazadaPmsEvt": ("travelhub.events.exchange", "evt.pms.rechazada"),
        "ReservaAprobadaManualEvt": ("travelhub.events.exchange", "evt.partnermanagement.aprobada"),
        "ReservaRechazadaManualEvt": ("travelhub.events.exchange", "evt.partnermanagement.rechazada"),
        "ReservaConfirmadaEvt": ("travelhub.events.exchange", "evt.reserva.confirmada"),
        "VoucherEnviadoEvt": ("travelhub.events.exchange", "evt.voucher.enviado"),
        "FalloEnvioVoucherEvt": ("travelhub.events.exchange", "evt.notification.fallo_envio"),
    }

    def _obtener_routing(self, tipo: str) -> tuple:
        if tipo in self.ROUTING_REGISTRY:
            return self.ROUTING_REGISTRY[tipo]

        # Fallbacks dinámicos
        if "Cmd" in tipo or "EsperandoVoucher" in tipo:
            if "LocalCmd" in tipo:
                routing_key = f"cmd.booking.{tipo.lower()}"
            else:
                routing_key = f"cmd.generico.{tipo.lower()}"
                logger.warning(f"[RabbitMQ] Tipo de comando '{tipo}' no mapeado formalmente. Usando '{routing_key}'")
            return "travelhub.commands.exchange", routing_key

        if "Evt" in tipo or tipo == "ReservaPendiente":
            routing_key = f"evt.generico.{tipo.lower()}"
            logger.warning(f"[RabbitMQ] Tipo de evento '{tipo}' no mapeado formalmente. Usando '{routing_key}'")
            return "travelhub.events.exchange", routing_key

        return "", ""

    # ------------------------------------------------------------------
    # Publicación
    # ------------------------------------------------------------------

    def _publicar_mensaje(self, payload_dict, topico_exchange, tipo_evento, routing_key):
        try:
            channel = self._get_channel()
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
            logger.info(f"[RabbitMQ] Publicado en '{topico_exchange}' [{routing_key}]: {tipo_evento}")
        except Exception as e:
            logger.error(f"[RabbitMQ] Error publicando mensaje '{tipo_evento}': {e}")

    def publicar_evento(self, evento, topico=""):
        # El parámetro topico de la interfaz original ahora se ignora en pro del enrutamiento dinámico

        from Booking.seedwork.aplicacion.comandos import Comando
        tipo = evento.__class__.__name__

        # Comandos pasados por la UoW como si fueran eventos
        if isinstance(evento, Comando):
            exchange, routing_key = self._obtener_routing(tipo)

            import uuid
            class UUIDEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, uuid.UUID):
                        return str(obj)
                    return json.JSONEncoder.default(self, obj)

            if hasattr(evento, '__dataclass_fields__'):
                payload = json.loads(json.dumps(asdict(evento), cls=UUIDEncoder))
            else:
                payload = json.loads(json.dumps(evento, cls=UUIDEncoder))

            logger.info(f"[RabbitMQ] Publicando CMD: {tipo}")
            if exchange and routing_key:
                self._publicar_mensaje(payload, exchange, tipo, routing_key)
            else:
                logger.warning(f"[RabbitMQ] No se pudo determinar el routing para comando directo {tipo}")
            return

        evento_integracion = self._mapeador.entidad_a_dto(evento)

        if evento_integracion:
            tipo = evento_integracion.type
            exchange, routing_key = self._obtener_routing(tipo)

            if exchange and routing_key:
                self._publicar_mensaje(evento_integracion.to_dict(), exchange, tipo, routing_key)
            else:
                logger.warning(f"[RabbitMQ] No se pudo determinar el routing para {tipo}")
        else:
            logger.info(f"[RabbitMQ] Evento de dominio {evento.__class__.__name__} ignorado (sin mapeo a Integración)")

    def publicar_comando(self, comando, routing_key: str):
        exchange = "travelhub.commands.exchange"
        payload = json.dumps(asdict(comando), default=str)
        try:
            channel = self._get_channel()
            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=payload,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.info(f"[RabbitMQ] Comando despachado a '{exchange}': {routing_key}")
        except Exception as e:
            logger.error(f"[RabbitMQ] Error publicando comando directo: {e}")
