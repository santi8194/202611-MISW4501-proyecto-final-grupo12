from __future__ import annotations
from dataclasses import dataclass, field
import datetime
import uuid

from Booking.seedwork.dominio.entidades import AgregacionRaiz, Entidad
from Booking.modulos.saga_reservas.dominio.objetos_valor import EstadoSaga, TipoMensajeSaga

@dataclass
class SagaExecutionLog(Entidad):
    id_instancia: uuid.UUID = field(default=None)
    tipo_mensaje: TipoMensajeSaga = field(default=TipoMensajeSaga.EVENTO_RECIBIDO)
    accion: str = field(default="")
    payload_snapshot: dict = field(default_factory=dict)
    fecha_registro: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class SagaInstance(AgregacionRaiz):
    id_reserva: uuid.UUID = field(default=None)
    id_flujo: str = field(default="RESERVA_ESTANDAR")
    version_ejecucion: int = field(default=1)
    estado_global: EstadoSaga = field(default=EstadoSaga.EN_PROCESO)
    paso_actual: int = field(default=0)
    fecha_creacion: datetime.datetime = field(default_factory=datetime.datetime.now)
    ultima_actualizacion: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    # Historial de ejecución para poder hacer compensación LIFO
    historial: list[SagaExecutionLog] = field(default_factory=list)

    def avanzar_paso(self, nuevo_paso: int, evento_recibido: str, payload: dict):
        self.paso_actual = nuevo_paso
        self.ultima_actualizacion = datetime.datetime.now()
        
        # Guardamos en el log el snapshot del evento que causó la transición
        log = SagaExecutionLog(
            id=uuid.uuid4(),
            id_instancia=self.id,
            tipo_mensaje=TipoMensajeSaga.EVENTO_RECIBIDO,
            accion=evento_recibido,
            payload_snapshot=payload
        )
        self.historial.append(log)

    def iniciar_compensacion(self, accion: str, payload_original: dict = None):
        self.estado_global = EstadoSaga.COMPENSANDO
        self.ultima_actualizacion = datetime.datetime.now()
        
        # Use provided payload or fallback to generic
        payload = {"id_reserva": str(self.id_reserva), "motivo": "Fallo reportado"}
        if payload_original:
            payload.update(payload_original)
            
        log = SagaExecutionLog(
            id=uuid.uuid4(),
            id_instancia=self.id,
            tipo_mensaje=TipoMensajeSaga.EVENTO_RECIBIDO,
            accion=accion,
            payload_snapshot=payload
        )
        self.historial.append(log)

    def registrar_comando_emitido(self, comando_nombre: str, payload: dict):
        log = SagaExecutionLog(
            id=uuid.uuid4(),
            id_instancia=self.id,
            tipo_mensaje=TipoMensajeSaga.COMANDO_EMITIDO,
            accion=comando_nombre,
            payload_snapshot=payload
        )
        self.historial.append(log)
