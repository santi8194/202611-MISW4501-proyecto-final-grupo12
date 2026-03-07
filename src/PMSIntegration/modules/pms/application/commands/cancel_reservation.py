from modules.pms.domain.events import PMSReservationCancelled


class CancelReservation:

    def __init__(self, repository, event_bus):
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, reservation_id):

        reservation = self.repository.obtain_by_id(reservation_id)

        if not reservation:
            return {"message": "Reservation not found"}

        reservation.state = "CANCELLED"

        self.repository.save(reservation)

        event = PMSReservationCancelled(
            reservation.id,
            reservation.booking_id
        )

        self.event_bus.publish_event(
            event.routing_key,
            event.type,
            event.to_dict()
        )

        return {
            "reservation_id": reservation.id,
            "state": reservation.state,
            "event_generated": event.type
        }