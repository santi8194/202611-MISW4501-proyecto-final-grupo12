import uuid

from Booking.seedwork.dominio.repositorios import Mapeador
from Booking.modulos.reserva.dominio.entidades import Reserva
from Booking.modulos.reserva.dominio.objetos_valor import EstadoReserva
from Booking.modulos.reserva.infraestructura.dto import ReservaDTO


class MapeadorReservaDTO(Mapeador):
    """
    Convierte entre la Entidad de dominio Reserva y su representación
    en base de datos ReservaDTO.
    """

    def obtener_tipo(self) -> type:
        return Reserva

    def entidad_a_dto(self, entidad: Reserva) -> ReservaDTO:
        return ReservaDTO(
            id=str(entidad.id),
            id_usuario=str(entidad.id_usuario),
            id_habitacion=str(entidad.id_habitacion),
            monto=entidad.monto,
            fecha_reserva=entidad.fecha_reserva,
            estado=entidad.estado.value,
            fecha_creacion=entidad.fecha_creacion,
            fecha_actualizacion=entidad.fecha_actualizacion
        )

    def dto_a_entidad(self, dto: ReservaDTO) -> Reserva:
        return Reserva(
            id=uuid.UUID(dto.id),
            id_usuario=uuid.UUID(dto.id_usuario),
            id_habitacion=uuid.UUID(dto.id_habitacion),
            monto=dto.monto,
            fecha_reserva=dto.fecha_reserva,
            estado=EstadoReserva(dto.estado),
            fecha_creacion=dto.fecha_creacion,
            fecha_actualizacion=dto.fecha_actualizacion
        )
