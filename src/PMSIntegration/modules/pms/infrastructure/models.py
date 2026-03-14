from sqlalchemy import Column, String, Integer
from .database import Base

class ReservationModel(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True)
    reservation_id = Column(String)
    room_id = Column(String)
    room_type = Column(String)
    guest_name = Column(String)
    state = Column(String)
    hotel_id = Column(String)
    fecha_reserva = Column(String)
    version = Column(Integer, nullable=False, default=1)

    # El control de concurrencia se hace a través de dos mecanismos:
    # 1. Lógica de aplicación: obtain_active_by_room_and_date() verifica si existe
    #    una reserva ACTIVA (no CANCELLED) para la misma habitación y fecha.
    #    Esto permite múltiples registros CANCELLED para el mismo (room_id, fecha_reserva).
    # 2. Bloqueo Optimista (Optimistic Locking): la columna 'version' delega en SQLAlchemy
    #    la detección de colisiones en escrituras concurrentes (StaleDataError).
    __mapper_args__ = {
        "version_id_col": version
    }