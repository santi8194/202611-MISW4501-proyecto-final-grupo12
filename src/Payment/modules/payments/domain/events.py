class SuccessfulPayment:
    def __init__(self, payment_id, reservation_id):
        self.type = "evt.pago.exitoso"
        self.payment_id = payment_id
        self.reservation_id = reservation_id
    def to_dict(self):
        return {
            "payment_id": self.payment_id,
            "reservation_id": self.reservation_id
        }

class FailedPayment:
    def __init__(self, reservation_id, reason):
        self.type = "evt.pago.rechazado"
        self.reservation_id = reservation_id
        self.reason = reason

    def to_dict(self):
        return {
            "reservation_id": self.reservation_id,
            "reason": self.reason
        }

class PaymentRefunded:
    def __init__(self, payment_id, reservation_id):
        self.type = "evt.pago.reembolsado"
        self.payment_id = payment_id
        self.reservation_id = reservation_id

    def to_dict(self):
        return {
            "payment_id": self.payment_id,
            "reservation_id": self.reservation_id
        }