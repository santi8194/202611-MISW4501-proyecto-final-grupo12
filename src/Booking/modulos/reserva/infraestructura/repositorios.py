from Booking.seedwork.dominio.repositorios import Repositorio
from Booking.modulos.reserva.dominio.entidades import Reserva
from Booking.modulos.reserva.infraestructura.dto import ReservaDTO
from Booking.modulos.reserva.infraestructura.mapeadores_dto import MapeadorReservaDTO
from Booking.config.db import db


class RepositorioReservas(Repositorio):

    def __init__(self):
        self._mapeador = MapeadorReservaDTO()

    def agregar(self, entidad: Reserva):
        reserva_dto = self._mapeador.entidad_a_dto(entidad)
        db.session.add(reserva_dto)

    def actualizar(self, entidad: Reserva):
        reserva_dto = db.session.query(ReservaDTO).filter_by(id=str(entidad.id)).first()
        if reserva_dto:
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
        return self._mapeador.dto_a_entidad(reserva_dto)

    def obtener_todos(self) -> list[Reserva]:
        dtos = db.session.query(ReservaDTO).all()
        return [self._mapeador.dto_a_entidad(dto) for dto in dtos]
