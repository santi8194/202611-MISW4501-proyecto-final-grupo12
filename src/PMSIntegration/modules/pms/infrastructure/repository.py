from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import ReservationModel


class ReservationRepository:

    def save(self, reservation):

        db: Session = SessionLocal()

        model = ReservationModel(
            id=reservation.id,
            booking_id=reservation.booking_id,
            hotel_id=reservation.hotel_id,
            room_type=reservation.room_type,
            guest_name=reservation.guest_name,
            state=reservation.state
        )

        db.merge(model)
        db.commit()
        db.close()


    def obtain_by_booking(self, booking_id):

        db: Session = SessionLocal()

        reservation = db.query(ReservationModel)\
            .filter(ReservationModel.booking_id == str(booking_id))\
            .first()

        db.close()
        return reservation


    def obtain_by_id(self, reservation_id):

        db: Session = SessionLocal()

        reservation = db.query(ReservationModel)\
            .filter(ReservationModel.id == str(reservation_id))\
            .first()

        db.close()
        return reservation