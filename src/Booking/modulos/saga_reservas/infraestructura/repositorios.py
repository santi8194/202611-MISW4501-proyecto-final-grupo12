from Booking.seedwork.dominio.repositorios import Repositorio
from Booking.modulos.saga_reservas.dominio.entidades import SagaInstance
from Booking.modulos.saga_reservas.infraestructura.dto import (
    SagaInstanceDTO, SagaExecutionLogDTO,
    SagaDefinitionDTO, SagaStepsDefinitionDTO
)
from Booking.modulos.saga_reservas.infraestructura.mapeadores import MapeadorSagaInstanceDTO
from Booking.config.db import db


class RepositorioSagas(Repositorio):

    def __init__(self):
        self._mapeador = MapeadorSagaInstanceDTO()

    def agregar(self, entidad: SagaInstance):
        dto = self._mapeador.entidad_a_dto(entidad)
        db.session.add(dto)

    def actualizar(self, entidad: SagaInstance):
        dto = db.session.query(SagaInstanceDTO).filter_by(id=str(entidad.id)).first()
        if dto:
            dto.version_ejecucion = entidad.version_ejecucion
            dto.estado_global = entidad.estado_global.value
            dto.paso_actual = entidad.paso_actual
            dto.ultima_actualizacion = entidad.ultima_actualizacion

            # Sincronizamos el historial: solo agregamos los logs nuevos
            ids_existentes = {log.id for log in dto.historial}
            for log in entidad.historial:
                if str(log.id) not in ids_existentes:
                    log_dto = SagaExecutionLogDTO(
                        id=str(log.id),
                        id_instancia=str(entidad.id),
                        tipo_mensaje=log.tipo_mensaje.value,
                        accion=log.accion,
                        payload_snapshot=log.payload_snapshot,
                        fecha_registro=log.fecha_registro
                    )
                    dto.historial.append(log_dto)

    def eliminar(self, entidad_id: str):
        db.session.query(SagaInstanceDTO).filter_by(id=entidad_id).delete()

    def obtener_por_id(self, id: str) -> SagaInstance:
        dto = db.session.query(SagaInstanceDTO).filter_by(id=id).first()
        if not dto:
            return None
        return self._mapeador.dto_a_entidad(dto)

    def obtener_todos(self) -> list:
        raise NotImplementedError("No soportado para sagas en este demo")

    def buscar_por_reserva(self, id_reserva: str) -> SagaInstance:
        dto = db.session.query(SagaInstanceDTO).filter_by(id_reserva=id_reserva).order_by(SagaInstanceDTO.fecha_creacion.desc()).first()
        if dto:
            return self.obtener_por_id(dto.id)
        return None

    def obtener_definicion_saga_activa(self, id_flujo: str) -> SagaDefinitionDTO:
        return db.session.query(SagaDefinitionDTO).filter_by(id_flujo=id_flujo, activo=True).first()

    def obtener_pasos_saga(self, id_flujo: str, version: int) -> list[SagaStepsDefinitionDTO]:
        return db.session.query(SagaStepsDefinitionDTO).filter_by(id_flujo=id_flujo, version=version).order_by(SagaStepsDefinitionDTO.index).all()
