import unittest
import uuid

from Booking.modulos.saga_reservas.dominio.entidades import SagaInstance
from Booking.modulos.saga_reservas.dominio.objetos_valor import EstadoSaga, TipoMensajeSaga

class TestSagaDominio(unittest.TestCase):
    
    def test_avanzar_paso_actualiza_index_y_registra_log(self):
        saga = SagaInstance(id=uuid.uuid4(), id_reserva=uuid.uuid4())
        
        self.assertEqual(saga.estado_global, EstadoSaga.EN_PROCESO)
        self.assertEqual(saga.paso_actual, 0)
        
        # Simular avance de paso en happy path
        saga.avanzar_paso(1, "ReservaCreadaIntegracionEvt", {"key": "value"})
        
        self.assertEqual(saga.paso_actual, 1)
        self.assertEqual(len(saga.historial), 1)
        
        ultimo_log = saga.historial[-1]
        self.assertEqual(ultimo_log.accion, "ReservaCreadaIntegracionEvt")
        self.assertEqual(ultimo_log.tipo_mensaje, TipoMensajeSaga.EVENTO_RECIBIDO)
        self.assertEqual(ultimo_log.payload_snapshot, {"key": "value"})

    def test_iniciar_compensacion_cambia_estado_a_compensando(self):
        saga = SagaInstance(id=uuid.uuid4(), id_reserva=uuid.uuid4())
        
        saga.iniciar_compensacion("PagoRechazadoEvt", {"motivo": "Saldo Insuficiente"})
        
        self.assertEqual(saga.estado_global, EstadoSaga.COMPENSANDO)
        self.assertEqual(len(saga.historial), 1)
        self.assertEqual(saga.historial[-1].accion, "PagoRechazadoEvt")

    def test_registrar_comando_emitido(self):
        saga = SagaInstance(id=uuid.uuid4(), id_reserva=uuid.uuid4())
        saga.registrar_comando_emitido("ProcesarPagoCmd", {"monto": 100})
        
        self.assertEqual(len(saga.historial), 1)
        self.assertEqual(saga.historial[-1].tipo_mensaje, TipoMensajeSaga.COMANDO_EMITIDO)
        self.assertEqual(saga.historial[-1].accion, "ProcesarPagoCmd")
