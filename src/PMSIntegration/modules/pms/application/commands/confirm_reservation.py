import random
import time

from modules.pms.infrastructure.repository import ReservationRepository
from modules.pms.infrastructure.event_bus import EventBus
from modules.pms.domain.entities import Reservation
from modules.pms.domain.events import (
    PMSReservationConfirmed,
    PMSReservationFailed
)


repository = ReservationRepository()
event_bus = EventBus()


class ConfirmReservation:

    def execute(self, booking_id, hotel_id, room_type, guest_name):

        existing = repository.obtain_by_booking(booking_id)
        if existing:
            return {
                "message": "Reservation already processed",
                "state": existing.state
            }

        time.sleep(0.5)

        try:

            if booking_id.endswith("5"):
                raise Exception("NO_AVAILABILITY")

            reservation = Reservation.create( booking_id, hotel_id, room_type, guest_name)

            repository.save(reservation)

            event = PMSReservationConfirmed( reservation.id, reservation.booking_id)
            event_bus.publish_event(event.type, event.to_dict())

        except Exception as e:
            event = PMSReservationFailed(booking_id, str(e))
            event_bus.publish_event(event.type, event.to_dict())

        return {
            "event_generated": event.type,
            "reservation_id": reservation.id if 'reservation' in locals() else "No reservation created - " +  event.reason,
        }