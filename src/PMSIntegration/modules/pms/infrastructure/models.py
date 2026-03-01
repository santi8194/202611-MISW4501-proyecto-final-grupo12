from sqlalchemy import Column, String
from .database import Base

class ReservationModel(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True)
    booking_id = Column(String)
    hotel_id = Column(String)
    room_type = Column(String)
    guest_name = Column(String)
    state = Column(String)