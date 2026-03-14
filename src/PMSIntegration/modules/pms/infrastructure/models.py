from sqlalchemy import Column, String, Integer, UniqueConstraint
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

    __table_args__ = (
        UniqueConstraint('room_id', 'fecha_reserva', name='_room_date_uc'),
    )

    __mapper_args__ = {
        "version_id_col": version
    }