from sqlalchemy import Column, String, Float
from .database import Base

class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    reservation_id = Column(String)
    amount = Column(Float)
    currency = Column(String)
    state = Column(String)