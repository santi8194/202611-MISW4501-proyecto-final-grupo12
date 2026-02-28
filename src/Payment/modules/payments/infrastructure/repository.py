class PaymentRepository:
    def __init__(self):
        self.payments = {}

    def save(self, payment):
        self.payments[payment.id] = payment

    def obtain_by_reservation(self, reservation_id):
        for payment in self.payments.values():
            if payment.reservation_id == reservation_id:
                return payment  
        return None