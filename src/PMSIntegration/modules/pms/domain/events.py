class PMSReservationConfirmed:

    def __init__(self, reservation_id, booking_id):
        self.type = "evt.reserva.confirmada"
        self.reservation_id = reservation_id
        self.booking_id = booking_id

    def to_dict(self):
        return {
            "reservation_id": self.reservation_id,
            "booking_id": self.booking_id
        }


class PMSReservationFailed:

    def __init__(self, booking_id, reason):
        self.type = "evt.reserva.rechazada"
        self.booking_id = booking_id
        self.reason = reason

    def to_dict(self):
        return {
            "booking_id": self.booking_id,
            "reason": self.reason
        }


class PMSReservationCancelled:

    def __init__(self, reservation_id, booking_id):
        self.type = "evt.reserva.cancelada"
        self.reservation_id = reservation_id
        self.booking_id = booking_id

    def to_dict(self):
        return {
            "reservation_id": self.reservation_id,
            "booking_id": self.booking_id
        }