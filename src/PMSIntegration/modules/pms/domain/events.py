class PMSReservationConfirmed:

    def __init__(self, pms_id, reservation_id):
        self.routing_key = "evt.pms.confirmacion_exitosa"
        self.type = "ConfirmacionPmsExitosaEvt"
        self.pms_id = pms_id
        self.reservation_id = reservation_id

    def to_dict(self):
        return {
            "codigo_pms": self.pms_id,
            "id_reserva": self.reservation_id
        }


class PMSReservationFailed:

    def __init__(self, reservation_id, reason):
        self.routing_key = "evt.pms.rechazada"
        self.type = "ReservaRechazadaPmsEvt"
        self.reservation_id = reservation_id
        self.reason = reason

    def to_dict(self):
        return {
            "id_reserva": self.reservation_id,
            "motivo": self.reason
        }


class PMSReservationCancelled:
    def __init__(self, reservation_id, room_id):
        self.routing_key = "evt.pms.reserva_cancelada"
        self.type = "ConfirmacionPmsCanceladaEvt"
        self.reservation_id = reservation_id
        self.room_id = room_id

    def to_dict(self):
        return {
            "id_habitacion": self.room_id,
            "id_reserva": self.reservation_id
        }