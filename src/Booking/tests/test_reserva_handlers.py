import unittest
from unittest.mock import MagicMock
import uuid

from Booking.modulos.reserva.aplicacion.handlers import (
    CrearReservaHoldHandler, 
    FormalizarReservaHandler,
    ConfirmarReservaLocalHandler,
    CancelarReservaLocalHandler
)
from Booking.modulos.reserva.aplicacion.comandos import (
    CrearReservaHold, 
    FormalizarReserva,
    ConfirmarReservaLocalCmd,
    CancelarReservaLocalCmd
)
from Booking.modulos.reserva.dominio.entidades import Reserva

class TestReservaHandlers(unittest.TestCase):
    def setUp(self):
        self.repositorio_mock = MagicMock()
        self.uow_mock = MagicMock()
        # Para que el UnitOfWork actue como un context manager (with self.uow:)
        self.uow_mock.__enter__ = MagicMock(return_value=self.uow_mock)
        self.uow_mock.__exit__ = MagicMock(return_value=None)

    def test_crear_reserva_hold_handler(self):
        handler = CrearReservaHoldHandler(repositorio=self.repositorio_mock, uow=self.uow_mock)
        comando = CrearReservaHold(
            id_usuario=uuid.uuid4(),
            id_habitacion=uuid.uuid4(),
            monto=300.0,
            fecha_reserva="2026-12-01"
        )
        
        id_reserva = handler.handle(comando)
        
        self.assertIsNotNone(id_reserva)
        self.repositorio_mock.agregar.assert_called_once()
        self.uow_mock.agregar_eventos.assert_called_once()
        self.uow_mock.commit.assert_called_once()

    def test_formalizar_reserva_handler(self):
        # Preparar un mock de reserva existente 
        reserva_mock = Reserva(id=uuid.uuid4())
        reserva_mock.iniciar_reserva_hold(uuid.uuid4(), uuid.uuid4(), 100.0, "2026-05-01")
        self.repositorio_mock.obtener_por_id.return_value = reserva_mock

        handler = FormalizarReservaHandler(repositorio=self.repositorio_mock, uow=self.uow_mock)
        comando = FormalizarReserva(id_reserva=reserva_mock.id)
        
        resultado = handler.handle(comando)
        
        self.assertTrue(resultado)
        self.repositorio_mock.actualizar.assert_called_once()
        self.uow_mock.commit.assert_called_once()

    def test_confirmar_reserva_local_handler(self):
        reserva_mock = Reserva(id=uuid.uuid4())
        reserva_mock.iniciar_reserva_hold(uuid.uuid4(), uuid.uuid4(), 100.0, "2026-05-01")
        reserva_mock.formalizar_y_pagar() # Pasarla a pendiente
        self.repositorio_mock.obtener_por_id.return_value = reserva_mock
        
        handler = ConfirmarReservaLocalHandler(repositorio=self.repositorio_mock, uow=self.uow_mock)
        comando = ConfirmarReservaLocalCmd(id_reserva=reserva_mock.id)
        
        evento = handler.handle(comando)
        
        self.assertEqual(evento.__class__.__name__, "ReservaConfirmadaEvt")
        self.repositorio_mock.actualizar.assert_called_once()
        self.uow_mock.commit.assert_called_once()
