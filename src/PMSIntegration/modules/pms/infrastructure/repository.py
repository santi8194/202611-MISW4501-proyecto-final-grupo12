from modules.pms.domain.entities import Reservation
from modules.pms.domain.repository import ReservationRepository
from modules.pms.infrastructure.model import Base, ReservationModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)


class ReservationRepositorySQL(ReservationRepository):

    def save(self, reservation: Reservation):
        session = Session()

        model = ReservationModel(
            id=str(reservation.id),
            booking_id=str(reservation.booking_id),
            hotel_id=reservation.hotel_id,
            room_type=reservation.room_type,
            guest_name=reservation.guest_name,
            state=reservation.state
        )

        session.add(model)
        session.commit()
        session.close()

        return model