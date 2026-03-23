import unittest
import uuid
from datetime import datetime

from Booking.modulos.reserva.dominio.entidades import Reserva
from Booking.modulos.reserva.dominio.objetos_valor import EstadoReserva

class TestReservaDominio(unittest.TestCase):
    def setUp(self):
        self.reserva = Reserva(id=uuid.uuid4())
        self.id_usuario = uuid.uuid4()
        self.id_habitacion = uuid.uuid4()
        self.monto = 150.0
        self.fecha_reserva = "2026-12-01"

    def test_iniciar_reserva_hold_cambia_estado_y_emite_evento(self):
        self.reserva.iniciar_reserva_hold(
            id_usuario=self.id_usuario,
            id_habitacion=self.id_habitacion,
            monto=self.monto,
            fecha_reserva=self.fecha_reserva
        )
        self.assertEqual(self.reserva.estado, EstadoReserva.HOLD)
        self.assertEqual(len(self.reserva.eventos), 1)
        self.assertEqual(self.reserva.eventos[0].__class__.__name__, "ReservaIniciada")

    def test_formalizar_reserva_desde_hold_cambia_a_pendiente(self):
        self.reserva.iniciar_reserva_hold(self.id_usuario, self.id_habitacion, self.monto, self.fecha_reserva)
        self.reserva.formalizar_y_pagar()
        
        self.assertEqual(self.reserva.estado, EstadoReserva.PENDIENTE)
        self.assertEqual(len(self.reserva.eventos), 2)
        self.assertEqual(self.reserva.eventos[-1].__class__.__name__, "ReservaPendiente")

    def test_formalizar_reserva_sin_hold_lanza_error(self):
        # La reserva inicia en HOLD por defecto en el constructor, pero simulemos un daño de estado
        self.reserva.estado = EstadoReserva.CANCELADA
        with self.assertRaises(ValueError):
            self.reserva.formalizar_y_pagar()

    def test_confirmar_reserva_desde_pendiente_cambia_a_confirmada(self):
        self.reserva.iniciar_reserva_hold(self.id_usuario, self.id_habitacion, self.monto, self.fecha_reserva)
        self.reserva.formalizar_y_pagar()
        self.reserva.confirmar_reserva()
        
        self.assertEqual(self.reserva.estado, EstadoReserva.CONFIRMADA)

    def test_cancelar_reserva(self):
        self.reserva.cancelar_reserva()
        self.assertEqual(self.reserva.estado, EstadoReserva.CANCELADA)
