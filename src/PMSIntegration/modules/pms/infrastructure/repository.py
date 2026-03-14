from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import ReservationModel


class ReservationRepository:

    def save(self, reservation):

        db: Session = SessionLocal()

        model = ReservationModel(
            id=reservation.id,
            reservation_id=reservation.reservation_id,
            room_id=reservation.room_id,
            room_type=reservation.room_type,
            guest_name=reservation.guest_name,
            hotel_id=reservation.hotel_id,
            fecha_reserva=reservation.fecha_reserva,
            state=reservation.state,
            version=reservation.version
        )

        db.merge(model)
        db.commit()
        db.close()

    def obtain_by_room_id(self, room_id):
        
        db: Session = SessionLocal()

        reservation = db.query(ReservationModel)\
            .filter(ReservationModel.room_id == room_id)\
            .first()
        db.close()
        return reservation

    def obtain_by_reservation_id(self, reservation_id):

        db: Session = SessionLocal()

        reservation = db.query(ReservationModel)\
            .filter(ReservationModel.reservation_id == str(reservation_id))\
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