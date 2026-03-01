from modules.pms.infrastructure.repository import ReservationRepository
from modules.pms.infrastructure.event_bus import EventBus
from modules.pms.domain.events import PMSReservationCancelled


repository = ReservationRepository()
event_bus = EventBus()


class CancelReservation:

    def execute(self, reservation_id):

        reservation = repository.obtain_by_id(reservation_id)

        if not reservation:
            return {"message": "Reservation not found"}

        reservation.state = "CANCELLED"
        repository.save(reservation)

        event = PMSReservationCancelled(
            reservation.id,
            reservation.booking_id
        )

        event_bus.publish(event.type, event.to_dict())

        return {
            "reservation_id": reservation.id,
            "state": reservation.state
        }