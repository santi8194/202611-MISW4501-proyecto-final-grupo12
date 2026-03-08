import time

from modules.pms.domain.entities import Reservation
from modules.pms.domain.events import (
    PMSReservationConfirmed,
    PMSReservationFailed
)

class ConfirmReservation:

    def __init__(self, repository, event_bus):
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, id_reserva, id_habitacion):

        existing_reservation = self.repository.obtain_by_reservation_id(id_reserva)

        print(f"[PMS] Checking existing reservation for id {id_reserva}: {'Found' if existing_reservation else 'Not found'}")

        if existing_reservation:
            return {
                "message": "Reservation already processed",
                "current_reservation_id": existing_reservation.reservation_id,
            }

        existing_room_reservation = self.repository.obtain_by_room_id(id_habitacion)
        print(f"[PMS] Checking existing reservation for room {id_habitacion}: {'Found' if existing_room_reservation else 'Not found'}")

        if existing_room_reservation and existing_room_reservation.state != "CANCELLED":
            print(f"[PMS] Room {id_habitacion} is already booked for reservation {existing_room_reservation.reservation_id}")
            event = PMSReservationFailed(
                id_reserva,
                "Room is already booked"
            )
            self.event_bus.publish_event(
                event.routing_key,
                event.type,
                event.to_dict()
            )
            return {
                "message": "Room is already booked",
                "state": existing_room_reservation.state
            }

        time.sleep(0.5)

        try:
            # simulación de fallo
            if id_reserva.endswith("5"):
                raise Exception("NO_AVAILABILITY")
            
            pmsReservation = Reservation.create(
                id_reserva,
                id_habitacion,
                "SUITE",
                "User123",
                "HotelXYZ",
            )

            self.repository.save(pmsReservation)

            event = PMSReservationConfirmed(
                pmsReservation.id,
                pmsReservation.reservation_id
            )

        except Exception as e:
            event = PMSReservationFailed(
                id_reserva,
                str(e)
            )

        self.event_bus.publish_event(
            event.routing_key,
            event.type,
            event.to_dict()
        )

        return {
            "event_generated": event.type,
            "pmscode": pmsReservation.id if 'pmsReservation' in locals()
            else f"No reservation created - {event.reason}"
        }