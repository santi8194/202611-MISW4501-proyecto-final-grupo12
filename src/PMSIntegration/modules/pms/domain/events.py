class PMSReservationConfirmed:

    def __init__(self, reservation_id, booking_id):
        self.routing_key = "evt.pms.confirmacion_exitosa"
        self.type = "ConfirmacionPmsExitosaEvt"
        self.reservation_id = reservation_id
        self.booking_id = booking_id

    def to_dict(self):
        return {
            "pms_code": self.reservation_id,
            "id_reserva": self.booking_id
        }


class PMSReservationFailed:

    def __init__(self, booking_id, reason):
        self.routing_key = "evt.pms.confirmacion_fallida"
        self.type = "ReservaRechazadaPmsEvt"
        self.booking_id = booking_id
        self.reason = reason

    def to_dict(self):
        return {
            "id_reserva": self.booking_id,
            "razon": self.reason
        }


class PMSReservationCancelled:

    def __init__(self, reservation_id, booking_id):
        self.routing_key = "evt.pms.reserva_cancelada"
        self.type = "ConfirmacionPmsCanceladaEvt"
        self.reservation_id = reservation_id
        self.booking_id = booking_id

    def to_dict(self):
        return {
            "pms_code": self.reservation_id,
            "id_reserva": self.booking_id
        }