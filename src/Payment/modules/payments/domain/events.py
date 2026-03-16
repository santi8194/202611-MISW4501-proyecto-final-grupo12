class SuccessfulPayment:
    def __init__(self, payment_id, reservation_id):
        self.routing_key = "evt.pago.exitoso"
        self.type = "PagoExitosoEvt"
        self.payment_id = payment_id
        self.reservation_id = reservation_id
    def to_dict(self):
        return {
            "token_pasarela": self.payment_id,
            "id_reserva": self.reservation_id
        }

class FailedPayment:
    def __init__(self, reservation_id, reason):
        self.routing_key = "evt.pago.rechazado"
        self.type = "PagoRechazadoEvt"
        self.reservation_id = reservation_id
        self.reason = reason

    def to_dict(self):
        return {
            "id_reserva": self.reservation_id,
            "motivo": self.reason
        }

class PaymentRefunded:
    def __init__(self, payment_id, reservation_id):
        self.routing_key = "evt.pago.reversado"
        self.type = "PagoReversadoEvt"
        self.payment_id = payment_id
        self.reservation_id = reservation_id

    def to_dict(self):
        return {
            "id_pago": self.payment_id,
            "id_reserva": self.reservation_id
        }
    
class PaymentRefundFailed:
    def __init__(self, reservation_id, reason):
        self.routing_key = "evt.pago.reverso_fallido"
        self.type = "PagoReversoFallidoEvt"
        self.reservation_id = reservation_id
        self.reason = reason

    def to_dict(self):
        return {
            "id_reserva": self.reservation_id,
            "motivo": self.reason
        }