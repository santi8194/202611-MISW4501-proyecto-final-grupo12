from modules.pms.domain.events import PMSReservationCancelled


class CancelReservation:

    def __init__(self, repository, event_bus):
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, reservation_id):

        reservation = self.repository.obtain_by_reservation_id(reservation_id)

        if not reservation:
            return {"message": "Reservation not found"}
        
        if reservation.state == "CANCELLED":
            return {"message": "Reservation is already cancelled"}

        reservation.state = "CANCELLED"

        # update() hace un UPDATE sobre la fila existente.
        # save() haría un INSERT (nuevo registro), que no es lo que queremos aquí.
        self.repository.update(reservation)

        event = PMSReservationCancelled(
            reservation.reservation_id,
            reservation.room_id
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