from sqlalchemy import Column, String
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ReservationModel(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True)
    booking_id = Column(String)
    hotel_id = Column(String)
    room_type = Column(String)
    guest_name = Column(String)
    state = Column(String)