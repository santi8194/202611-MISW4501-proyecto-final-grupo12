import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from modules.pms.domain.entities import Reservation
from modules.pms.domain.events import (
    PMSReservationConfirmed,
    PMSReservationFailed
)

class ConfirmReservation:

    def __init__(self, repository, event_bus):
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, id_reserva, id_habitacion, fecha_reserva):

        existing_reservation = self.repository.obtain_by_reservation_id(id_reserva)

        print(f"[PMS] Checking existing reservation for id {id_reserva}: {'Found' if existing_reservation else 'Not found'}")

        if existing_reservation:
            return {
                "message": "Reservation already processed",
                "current_reservation_id": existing_reservation.reservation_id,
            }

        # Validación de overbooking: Búsqueda por habitación + fecha + estado activo.
        # Un estado CANCELLED no bloquea la habitación, lo que permite re-reservar una habitación
        # que fue previamente cancelada para la misma fecha.
        active_booking = self.repository.obtain_active_by_room_and_date(id_habitacion, fecha_reserva)
        if active_booking:
            print(f"[PMS] Room {id_habitacion} is already ACTIVELY booked on {fecha_reserva} (State: {active_booking.state})")
            pms_event = PMSReservationFailed(
                reservation_id=id_reserva,
                reason=f"Protección contra overbooking: Habitación ya confirmada para la fecha {fecha_reserva}.",
                fecha_reserva=fecha_reserva
            )
            self.event_bus.publish_event(
                routing_key=pms_event.routing_key,
                event_type=pms_event.type,
                payload=pms_event.to_dict()
            )
            return {
                "message": "Room is already actively booked for this date",
                "state": active_booking.state
            }

        ##time.sleep(0.5)

        try:
            pmsReservation = Reservation.create(
                id_reserva,
                id_habitacion,
                "SUITE",
                "User123",
                "HotelXYZ",
                fecha_reserva
            )

            self.repository.save(pmsReservation)

            # 4. Generar evento de éxito
            pms_event = PMSReservationConfirmed(
                pms_id=pmsReservation.id,
                reservation_id=id_reserva,
                fecha_reserva=fecha_reserva
            )
            # CRÍTICO: El parámetro debe ser 'payload', NO 'data'
            self.event_bus.publish_event(
                routing_key=pms_event.routing_key,
                event_type=pms_event.type,
                payload=pms_event.to_dict()
            )

            return pms_event.to_dict()

        except IntegrityError:
            print(f"[PMS] IntegrityError caught for room {id_habitacion} on {fecha_reserva}. Overbooking avoided.")
            
            pms_event = PMSReservationFailed(
                reservation_id=id_reserva,
                reason="Protección contra overbooking: Habitación ya reservada para esta fecha.",
                fecha_reserva=fecha_reserva
            )
        except StaleDataError:
            print(f"[PMS] StaleDataError caught for room {id_habitacion}. Overbooking avoided.")
            pms_event = PMSReservationFailed(
                reservation_id=id_reserva,
                reason="Protección contra overbooking: Habitación ya reservada para esta fecha.",
                fecha_reserva=fecha_reserva
            )
        except Exception as e:
            # Captura cualquier otro error (ej: fallo de conexión a RabbitMQ) y genera evento de fallo
            print(f"[PMS] Error inesperado: {str(e)}")
            pms_event = PMSReservationFailed(
                reservation_id=id_reserva,
                reason=str(e),
                fecha_reserva=fecha_reserva
            )

        # Publicar evento de fallo con parámetro 'payload'
        self.event_bus.publish_event(
            routing_key=pms_event.routing_key,
            event_type=pms_event.type,
            payload=pms_event.to_dict()
        )

        return {
            "event_generated": pms_event.type,
            "motivo": pms_event.reason,
            "id_reserva": id_reserva
        }