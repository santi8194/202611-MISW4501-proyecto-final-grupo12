from Booking.seedwork.dominio.repositorios import Repositorio
from Booking.modulos.saga_reservas.dominio.entidades import SagaInstance, SagaExecutionLog
from Booking.modulos.saga_reservas.dominio.objetos_valor import EstadoSaga, TipoMensajeSaga
from Booking.modulos.saga_reservas.infraestructura.dto import (
    SagaInstanceDTO, SagaExecutionLogDTO, 
    SagaDefinitionDTO, SagaStepsDefinitionDTO
)
from Booking.config.db import db
import uuid

class RepositorioSagas(Repositorio):
    
    def agregar(self, entidad: SagaInstance):
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
            log_dto = SagaExecutionLogDTO(
                id=str(log.id),
                id_instancia=str(entidad.id),
                tipo_mensaje=log.tipo_mensaje.value,
                accion=log.accion,
                payload_snapshot=log.payload_snapshot,
                fecha_registro=log.fecha_registro
            )
            dto.historial.append(log_dto)
        
        db.session.add(dto)

    def actualizar(self, entidad: SagaInstance):
        dto = db.session.query(SagaInstanceDTO).filter_by(id=str(entidad.id)).first()
        if dto:
            dto.version_ejecucion = entidad.version_ejecucion
            dto.estado_global = entidad.estado_global.value
            dto.paso_actual = entidad.paso_actual
            dto.ultima_actualizacion = entidad.ultima_actualizacion
            
            # Sincronizamos el historial (simplificado, solo agregamos los nuevos)
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
        
        historial = [
            SagaExecutionLog(
                id=uuid.UUID(l.id),
                id_instancia=uuid.UUID(l.id_instancia),
                tipo_mensaje=TipoMensajeSaga(l.tipo_mensaje),
                accion=l.accion,
                payload_snapshot=l.payload_snapshot,
                fecha_registro=l.fecha_registro
            ) for l in dto.historial
        ]
        
        # Ojo: Mantenemos el orden por fecha_registro para asegurar el LIFO!
        historial.sort(key=lambda x: x.fecha_registro)

        saga = SagaInstance(
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
        return saga

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
