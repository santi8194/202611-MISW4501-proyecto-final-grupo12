from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import ReservationModel


class ReservationRepository:

    def save(self, reservation):
        """
        Persiste la reserva en la base de datos. 
        Utiliza control de persistencia optimista a través de la columna 'version'.
        Si otra transacción modificó el registro entre la lectura y la escritura, 
        SQLAlchemy lanzará una StaleDataError.
        """
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
            # La versión es manejada por el Agregado de Dominio e incrementada por SQLAlchemy
            version=reservation.version 
        )

        try:
            # merge() sincroniza el estado del objeto con la sesión, disparando
            # la validación de versión si el registro ya existe.
            db.merge(model)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def obtain_by_room_id(self, room_id):
        """
        Busca reservas por habitación. 
        Útil para auditoría o validaciones generales, aunque la validación 
        de ocupación principal se delega al método obtain_active_by_room_and_date.
        """
        db: Session = SessionLocal()
        reservation = db.query(ReservationModel)\
            .filter(ReservationModel.room_id == room_id)\
            .first()
        db.close()
        return reservation

    def obtain_active_by_room_and_date(self, room_id, fecha_reserva):
        """
        Búsqueda específica para validar overbooking:
        Retorna una reserva CONFIRMADA para esa habitación en esa fecha.
        Si la reserva existente está CANCELADA (state='CANCELLED'), retorna None,
        permitiendo así re-reservar el mismo cuarto en la misma fecha.
        """
        db: Session = SessionLocal()
        reservation = db.query(ReservationModel)\
            .filter(
                ReservationModel.room_id == room_id,
                ReservationModel.fecha_reserva == fecha_reserva,
                ReservationModel.state != "CANCELLED"
            )\
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