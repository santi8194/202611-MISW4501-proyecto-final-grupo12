from Booking.seedwork.dominio.repositorios import Repositorio
from Booking.modulos.reserva.dominio.entidades import Reserva
from Booking.modulos.reserva.dominio.objetos_valor import EstadoReserva
from Booking.modulos.reserva.infraestructura.dto import ReservaDTO
from Booking.config.db import db
import uuid

class RepositorioReservas(Repositorio):
    
    def agregar(self, entidad: Reserva):
        # Mapeo Entidad de Dominio -> DTO de Infraestructura
        reserva_dto = ReservaDTO(
            id=str(entidad.id),
            id_usuario=str(entidad.id_usuario),
            id_habitacion=str(entidad.id_habitacion),
            monto=entidad.monto,
            fecha_reserva=entidad.fecha_reserva,
            estado=entidad.estado.value,
            fecha_creacion=entidad.fecha_creacion,
            fecha_actualizacion=entidad.fecha_actualizacion
        )
        db.session.add(reserva_dto)

    def actualizar(self, entidad: Reserva):
        # Recuperamos el DTO
        reserva_dto = db.session.query(ReservaDTO).filter_by(id=str(entidad.id)).first()
        if reserva_dto:
            # Actualizamos las propiedades que pueden cambiar
            reserva_dto.estado = entidad.estado.value
            reserva_dto.fecha_actualizacion = entidad.fecha_actualizacion
            reserva_dto.fecha_reserva = entidad.fecha_reserva
            # La base de datos guarda los cambios cuando se llama a uow.commit()

    def eliminar(self, entidad_id: str):
        db.session.query(ReservaDTO).filter_by(id=entidad_id).delete()

    def obtener_por_id(self, id: str) -> Reserva:
        reserva_dto = db.session.query(ReservaDTO).filter_by(id=id).first()
        if not reserva_dto:
            return None
        
        # Mapeo DTO -> Entidad de Dominio
        reserva = Reserva(
            id=uuid.UUID(reserva_dto.id),
            id_usuario=uuid.UUID(reserva_dto.id_usuario),
            id_habitacion=uuid.UUID(reserva_dto.id_habitacion),
            monto=reserva_dto.monto,
            fecha_reserva=reserva_dto.fecha_reserva,
            estado=EstadoReserva(reserva_dto.estado),
            fecha_creacion=reserva_dto.fecha_creacion,
            fecha_actualizacion=reserva_dto.fecha_actualizacion
        )
        return reserva

    def obtener_todos(self) -> list[Reserva]:
        dtos = db.session.query(ReservaDTO).all()
        reservas = []
        for dto in dtos:
            reservas.append(Reserva(
                id=uuid.UUID(dto.id),
                id_usuario=uuid.UUID(dto.id_usuario),
                id_habitacion=uuid.UUID(dto.id_habitacion),
                monto=dto.monto,
                fecha_reserva=dto.fecha_reserva,
                estado=EstadoReserva(dto.estado),
                fecha_creacion=dto.fecha_creacion,
                fecha_actualizacion=dto.fecha_actualizacion
            ))
        return reservas
