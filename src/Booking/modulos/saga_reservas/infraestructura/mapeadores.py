import uuid

from Booking.seedwork.dominio.repositorios import Mapeador
from Booking.modulos.saga_reservas.dominio.entidades import SagaInstance, SagaExecutionLog
from Booking.modulos.saga_reservas.dominio.objetos_valor import EstadoSaga, TipoMensajeSaga
from Booking.modulos.saga_reservas.infraestructura.dto import SagaInstanceDTO, SagaExecutionLogDTO


class MapeadorSagaLogDTO:
    """Convierte SagaExecutionLog ↔ SagaExecutionLogDTO."""

    def log_a_dto(self, log: SagaExecutionLog, id_instancia: str) -> SagaExecutionLogDTO:
        return SagaExecutionLogDTO(
            id=str(log.id),
            id_instancia=id_instancia,
            tipo_mensaje=log.tipo_mensaje.value,
            accion=log.accion,
            payload_snapshot=log.payload_snapshot,
            fecha_registro=log.fecha_registro
        )

    def dto_a_log(self, dto: SagaExecutionLogDTO) -> SagaExecutionLog:
        return SagaExecutionLog(
            id=uuid.UUID(dto.id),
            id_instancia=uuid.UUID(dto.id_instancia),
            tipo_mensaje=TipoMensajeSaga(dto.tipo_mensaje),
            accion=dto.accion,
            payload_snapshot=dto.payload_snapshot,
            fecha_registro=dto.fecha_registro
        )


class MapeadorSagaInstanceDTO(Mapeador):
    """
    Convierte entre la Entidad de dominio SagaInstance y su representación
    en base de datos SagaInstanceDTO (incluyendo su historial de logs).
    """

    def __init__(self):
        self._log_mapeador = MapeadorSagaLogDTO()

    def obtener_tipo(self) -> type:
        return SagaInstance

    def entidad_a_dto(self, entidad: SagaInstance) -> SagaInstanceDTO:
        dto = SagaInstanceDTO(
            id=str(entidad.id),
            id_reserva=str(entidad.id_reserva),
            id_flujo=entidad.id_flujo,
            version_ejecucion=entidad.version_ejecucion,
            estado_global=entidad.estado_global.value,
            paso_actual=entidad.paso_actual,
            fecha_creacion=entidad.fecha_creacion,
            ultima_actualizacion=entidad.ultima_actualizacion
        )
        for log in entidad.historial:
            dto.historial.append(self._log_mapeador.log_a_dto(log, str(entidad.id)))
        return dto

    def dto_a_entidad(self, dto: SagaInstanceDTO) -> SagaInstance:
        historial = [self._log_mapeador.dto_a_log(l) for l in dto.historial]
        # Ordenamos por fecha para garantizar LIFO correcto
        historial.sort(key=lambda x: x.fecha_registro)
        return SagaInstance(
            id=uuid.UUID(dto.id),
            id_reserva=uuid.UUID(dto.id_reserva),
            id_flujo=dto.id_flujo,
            version_ejecucion=dto.version_ejecucion,
            estado_global=EstadoSaga(dto.estado_global),
            paso_actual=dto.paso_actual,
            fecha_creacion=dto.fecha_creacion,
            ultima_actualizacion=dto.ultima_actualizacion,
            historial=historial
        )
