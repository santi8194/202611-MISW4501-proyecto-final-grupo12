import random
import time

from modules.payments.domain.entities import Payment
from modules.payments.domain.events import SuccessfulPayment, FailedPayment
from modules.payments.infrastructure.repository import PaymentRepository


repository = PaymentRepository()

class ProcessPayment:

    def execute(self, reservation_id: str, amount: float, currency: str):

        existing_payment = repository.obtain_by_reservation(reservation_id)
        if existing_payment:
            return {"message": "Payment already processed", "state": existing_payment.state}

        payment = Payment(reservation_id, amount, currency)

        time.sleep(0.5)

        # Simulación 80% éxito
        if random.random() > 0.2:
            payment.aprobar()
            repository.save(payment)
            event = SuccessfulPayment(payment.id, payment.reservation_id)
        else:
            payment.rechazar()
            repository.save(payment)
            event = FailedPayment(payment.reservation_id, "Funds insufficient")

        return {
            "payment_id": payment.id,
            "state": payment.state,
            "event_generated": event.type
        }