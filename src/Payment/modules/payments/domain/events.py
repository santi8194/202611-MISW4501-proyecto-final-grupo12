class SuccessfulPayment:
    def __init__(self, payment_id, reservation_id):
        self.type = "SuccessfulPaymentEvt"
        self.payment_id = payment_id
        self.reservation_id = reservation_id

class FailedPayment:
    def __init__(self, reservation_id, reason):
        self.type = "FailedPaymentEvt"
        self.reservation_id = reservation_id
        self.reason = reason