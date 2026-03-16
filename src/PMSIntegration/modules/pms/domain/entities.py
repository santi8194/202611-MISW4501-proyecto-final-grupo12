from uuid import uuid4, UUID
from dataclasses import dataclass


@dataclass
class Reservation:
    id: UUID
    reservation_id: UUID
    room_id: str
    room_type: str
    guest_name: str
    hotel_id: str
    fecha_reserva: str
    state: str
    version: int = 1

    @staticmethod
    def create(reservation_id, room_id, room_type, guest_name, hotel_id, fecha_reserva):
        return Reservation(
            id=str(uuid4()),
            reservation_id=str(reservation_id),
            room_id=room_id,
            room_type=room_type,
            guest_name=guest_name,
            hotel_id=hotel_id,
            fecha_reserva=fecha_reserva,
            state="CONFIRMED",
            version=1
        )
    
    def cancel(self):
        self.state = "CANCELED"