class PMSReservationConfirmed:

    def __init__(self, pms_id, reservation_id, fecha_reserva=None):
        self.routing_key = "evt.pms.confirmacion_exitosa"
        self.type = "ConfirmacionPmsExitosaEvt"
        self.pms_id = pms_id
        self.reservation_id = reservation_id
        self.fecha_reserva = fecha_reserva

    def to_dict(self):
        return {
            "codigo_pms": self.pms_id,
            "id_reserva": self.reservation_id,
            "fecha_reserva": self.fecha_reserva
        }


class PMSReservationFailed:

    def __init__(self, reservation_id, reason, fecha_reserva=None):
        self.routing_key = "evt.pms.rechazada"
        self.type = "ReservaRechazadaPmsEvt"
        self.reservation_id = reservation_id
        self.reason = reason
        self.fecha_reserva = fecha_reserva

    def to_dict(self):
        return {
            "id_reserva": self.reservation_id,
            "motivo": self.reason,
            "fecha_reserva": self.fecha_reserva
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