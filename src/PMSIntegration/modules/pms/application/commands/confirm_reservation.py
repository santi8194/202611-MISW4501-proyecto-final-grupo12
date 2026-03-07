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

        existing = self.repository.obtain_by_booking(id_reserva)

        if existing:
            return {
                "message": "Reservation already processed",
                "state": existing.state
            }

        time.sleep(0.5)

        try:

            # simulación de fallo
            if id_reserva.endswith("5"):
                raise Exception("NO_AVAILABILITY")

            reservation = Reservation.create(
                id_reserva,
                id_habitacion,
                "SUITE",
                "User123"
            )

            self.repository.save(reservation)

            event = PMSReservationConfirmed(
                reservation.id,
                reservation.booking_id
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
            "reservation_id": reservation.id if 'reservation' in locals()
            else f"No reservation created - {event.reason}"
        }