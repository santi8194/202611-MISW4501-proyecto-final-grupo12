

from modules.pms.domain.entities import Reservation
from modules.pms.infrastructure.external_services import PMSMock
from modules.pms.infrastructure.repository import ReservationRepositorySQL


class PMSService:

    def __init__(self):
        self.repo = ReservationRepositorySQL()

    def create_reservation(self, booking_id, hotel_id, room_type, guest_name):

        availability = PMSMock.check_availability(hotel_id, room_type)

        if not availability:
            raise Exception("There are no available rooms of the requested type")

        reservation = Reservation.create(
            booking_id=booking_id,
            hotel_id=hotel_id,
            room_type=room_type,
            guest_name=guest_name
        )

        self.repo.save(reservation)

        return {
            "reservation_id": reservation.id,
            "state": reservation.state
        }