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

    def execute(self, booking_id, hotel_id, room_type, guest_name):

        existing = self.repository.obtain_by_booking(booking_id)

        if existing:
            return {
                "message": "Reservation already processed",
                "state": existing.state
            }

        time.sleep(0.5)

        try:

            # simulación de fallo
            if booking_id.endswith("5"):
                raise Exception("NO_AVAILABILITY")

            reservation = Reservation.create(
                booking_id,
                hotel_id,
                room_type,
                guest_name
            )

            self.repository.save(reservation)

            event = PMSReservationConfirmed(
                reservation.id,
                reservation.booking_id
            )

        except Exception as e:

            event = PMSReservationFailed(
                booking_id,
                str(e)
            )

        self.event_bus.publish_event(
            event.type,
            event.to_dict()
        )

        return {
            "event_generated": event.type,
            "reservation_id": reservation.id if 'reservation' in locals()
            else f"No reservation created - {event.reason}"
        }