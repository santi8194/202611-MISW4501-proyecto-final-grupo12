from uuid import uuid4, UUID
from dataclasses import dataclass


@dataclass
class Reservation:
    id: UUID
    booking_id: UUID
    hotel_id: str
    room_type: str
    guest_name: str
    state: str

    @staticmethod
    def create(booking_id, hotel_id, room_type, guest_name):
        return Reservation(
            id=str(uuid4()),
            booking_id=str(booking_id),
            hotel_id=hotel_id,
            room_type=room_type,
            guest_name=guest_name,
            state="CONFIRMED"
        )
    
    def cancel(self):
        self.state = "CANCELED"