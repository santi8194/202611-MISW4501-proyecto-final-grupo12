from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import ReservationModel


class ReservationRepository:

    def save(self, reservation):
        """
        Persiste una NUEVA reserva en la base de datos.

        Estrategia de concurrencia (doble capa):
        1. Pre-validación (aplicación): obtain_active_by_room_and_date() rechaza
           el intento si ya existe una reserva ACTIVA para (room_id, fecha_reserva).
           Permite acumular N registros CANCELLED en la misma fecha y habitación.
        2. Índice único parcial (PostgreSQL): capa de seguridad final que bloquea
           atómicamente cualquier INSERT que viole la regla. Elimina TOCTOU.
           Definido en models.py: UNIQUE(room_id, fecha_reserva) WHERE state != 'CANCELLED'.
        3. Bloqueo Optimista (version): protege UPDATEs concurrentes al mismo registro.
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
            version=reservation.version
        )
        try:
            # add() porque es siempre un INSERT nuevo (UUID único por reserva).
            # merge() haría upsert sobre el PK, lo cual no es el comportamiento deseado.
            db.add(model)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def update(self, reservation):
        """
        Actualiza el estado de una reserva EXISTENTE en la base de datos.
        Usado para cambios de estado como CONFIRMED -> CANCELLED.
        Usa merge() para sincronizar el objeto con la sesión y hacer el UPDATE.
        La columna 'version' activa el Bloqueo Optimista: si el registro fue
        modificado por otra transacción concurrente, SQLAlchemy lanzará StaleDataError.
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
            version=reservation.version
        )
        try:
            # merge() hace el UPDATE sobre el registro existente identificado por el PK (id).
            # Si la versión no coincide, SQLAlchemy lanza StaleDataError (Optimistic Locking).
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