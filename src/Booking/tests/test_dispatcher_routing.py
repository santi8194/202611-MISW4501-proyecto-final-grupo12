import unittest
from unittest.mock import MagicMock, patch

from Booking.seedwork.infraestructura.dispatchers import DespachadorRabbitMQ
from Booking.seedwork.aplicacion.comandos import Comando
from Booking.seedwork.dominio.eventos import EventoDominio
from dataclasses import dataclass
import uuid


# --- Fixtures mínimos para testear el routing sin RabbitMQ ---

@dataclass
class ProcesarPagoCmd(Comando):
    id_reserva: uuid.UUID
    monto: float = 100.0

@dataclass
class ConfirmarReservaPmsCmd(Comando):
    id_reserva: uuid.UUID
    id_habitacion: uuid.UUID = None
    fecha_reserva: str = None

@dataclass
class ReversarPagoCmd(Comando):
    id_reserva: uuid.UUID
    monto: float = 0.0

@dataclass
class CancelarReservaPmsCmd(Comando):
    id_reserva: uuid.UUID
    id_habitacion: uuid.UUID = None

@dataclass
class SolicitarAprobacionManualCmd(Comando):
    id_reserva: uuid.UUID
    id_habitacion: uuid.UUID = None

@dataclass
class ComandoDesconocidoCmd(Comando):
    id_reserva: uuid.UUID = None


class TestRoutingRegistry(unittest.TestCase):
    """
    R13: Verifica que cada tipo de mensaje conocido resuelva al exchange
    y routing_key correctos mediante el ROUTING_REGISTRY del DespachadorRabbitMQ.
    """

    def setUp(self):
        self.dispatcher = DespachadorRabbitMQ(mapeador_eventos=None)

    # --- Comandos conocidos ---
    def test_procesar_pago_cmd_routing(self):
        exchange, key = self.dispatcher._obtener_routing("ProcesarPagoCmd")
        self.assertEqual(exchange, "travelhub.commands.exchange")
        self.assertEqual(key, "cmd.payment.procesar-pago")

    def test_confirmar_reserva_pms_cmd_routing(self):
        exchange, key = self.dispatcher._obtener_routing("ConfirmarReservaPmsCmd")
        self.assertEqual(exchange, "travelhub.commands.exchange")
        self.assertEqual(key, "cmd.pms.confirmar-reserva")

    def test_reversar_pago_cmd_routing(self):
        exchange, key = self.dispatcher._obtener_routing("ReversarPagoCmd")
        self.assertEqual(exchange, "travelhub.commands.exchange")
        self.assertEqual(key, "cmd.payment.reversar-pago")

    def test_cancelar_reserva_pms_cmd_routing(self):
        exchange, key = self.dispatcher._obtener_routing("CancelarReservaPmsCmd")
        self.assertEqual(exchange, "travelhub.commands.exchange")
        self.assertEqual(key, "cmd.pms.cancelar-reserva")

    def test_solicitar_aprobacion_manual_cmd_routing(self):
        exchange, key = self.dispatcher._obtener_routing("SolicitarAprobacionManualCmd")
        self.assertEqual(exchange, "travelhub.commands.exchange")
        self.assertEqual(key, "cmd.partnermanagement.solicitar-aprobacion")

    # --- Eventos conocidos ---
    def test_reserva_creada_integracion_evt_routing(self):
        exchange, key = self.dispatcher._obtener_routing("ReservaCreadaIntegracionEvt")
        self.assertEqual(exchange, "travelhub.events.exchange")
        self.assertEqual(key, "evt.reserva.creada")

    def test_pago_exitoso_evt_routing(self):
        exchange, key = self.dispatcher._obtener_routing("PagoExitosoEvt")
        self.assertEqual(exchange, "travelhub.events.exchange")
        self.assertEqual(key, "evt.pago.exitoso")

    def test_pago_rechazado_evt_routing(self):
        exchange, key = self.dispatcher._obtener_routing("PagoRechazadoEvt")
        self.assertEqual(exchange, "travelhub.events.exchange")
        self.assertEqual(key, "evt.pago.rechazado")

    def test_confirmacion_pms_exitosa_evt_routing(self):
        exchange, key = self.dispatcher._obtener_routing("ConfirmacionPmsExitosaEvt")
        self.assertEqual(exchange, "travelhub.events.exchange")
        self.assertEqual(key, "evt.pms.confirmacion_exitosa")

    def test_reserva_rechazada_pms_evt_routing(self):
        exchange, key = self.dispatcher._obtener_routing("ReservaRechazadaPmsEvt")
        self.assertEqual(exchange, "travelhub.events.exchange")
        self.assertEqual(key, "evt.pms.rechazada")

    def test_reserva_confirmada_evt_routing(self):
        exchange, key = self.dispatcher._obtener_routing("ReservaConfirmadaEvt")
        self.assertEqual(exchange, "travelhub.events.exchange")
        self.assertEqual(key, "evt.reserva.confirmada")

    def test_voucher_enviado_evt_routing(self):
        exchange, key = self.dispatcher._obtener_routing("VoucherEnviadoEvt")
        self.assertEqual(exchange, "travelhub.events.exchange")
        self.assertEqual(key, "evt.voucher.enviado")

    def test_fallo_envio_voucher_evt_routing(self):
        exchange, key = self.dispatcher._obtener_routing("FalloEnvioVoucherEvt")
        self.assertEqual(exchange, "travelhub.events.exchange")
        self.assertEqual(key, "evt.notification.fallo_envio")

    # --- Fallbacks dinámicos ---
    def test_comando_local_desconocido_usa_fallback_booking(self):
        exchange, key = self.dispatcher._obtener_routing("CualquierLocalCmd")
        self.assertEqual(exchange, "travelhub.commands.exchange")
        self.assertTrue(key.startswith("cmd.booking."))

    def test_comando_generico_desconocido_usa_fallback(self):
        exchange, key = self.dispatcher._obtener_routing("MiComandoRaroCmd")
        self.assertEqual(exchange, "travelhub.commands.exchange")
        self.assertTrue(key.startswith("cmd.generico."))

    def test_evento_generico_desconocido_usa_fallback(self):
        exchange, key = self.dispatcher._obtener_routing("MiEventoRaroEvt")
        self.assertEqual(exchange, "travelhub.events.exchange")
        self.assertTrue(key.startswith("evt.generico."))

    def test_tipo_completamente_desconocido_retorna_vacio(self):
        exchange, key = self.dispatcher._obtener_routing("ClaseRandom")
        self.assertEqual(exchange, "")
        self.assertEqual(key, "")

    # --- Cobertura del ROUTING_REGISTRY completo ---
    def test_todos_los_registros_tienen_exchange_y_routing_key_validos(self):
        for tipo, (exchange, key) in DespachadorRabbitMQ.ROUTING_REGISTRY.items():
            with self.subTest(tipo=tipo):
                self.assertTrue(exchange.startswith("travelhub."), f"Exchange inválido para {tipo}: {exchange}")
                self.assertTrue(len(key) > 0, f"Routing key vacía para {tipo}")
                self.assertIn(".", key, f"Routing key sin jerarquía para {tipo}: {key}")

    # --- Publicación sin conexión real (mock de la conexión) ---
    @patch("Booking.seedwork.infraestructura.dispatchers.pika.BlockingConnection")
    def test_publicar_evento_comando_llama_basic_publish(self, mock_connection_cls):
        mock_channel = MagicMock()
        mock_connection = MagicMock()
        mock_connection.is_closed = False
        mock_connection.channel.return_value = mock_channel
        mock_connection_cls.return_value = mock_connection

        dispatcher = DespachadorRabbitMQ(mapeador_eventos=None)
        cmd = ProcesarPagoCmd(id_reserva=uuid.uuid4(), monto=200.0)

        dispatcher.publicar_evento(cmd)

        mock_channel.basic_publish.assert_called_once()
        call_kwargs = mock_channel.basic_publish.call_args[1]
        self.assertEqual(call_kwargs["exchange"], "travelhub.commands.exchange")
        self.assertEqual(call_kwargs["routing_key"], "cmd.payment.procesar-pago")

        dispatcher.cerrar()
