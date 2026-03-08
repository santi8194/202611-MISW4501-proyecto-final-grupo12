import time

from modules.payments.domain.entities import Payment
from modules.payments.domain.events import SuccessfulPayment, FailedPayment


class ProcessPayment:

    def __init__(self, repository, event_bus):
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, reservation_id: str, amount: float):

        existing_payment = self.repository.obtain_by_reservation(reservation_id)

        if existing_payment:
            return {
                "message": "Payment already processed",
                "state": existing_payment.state
            }

        payment = Payment(reservation_id, amount, "USD")

        # simulación de procesamiento
        time.sleep(0.5)

        if amount < 5000:

            payment.approve()
            self.repository.save(payment)

            event = SuccessfulPayment(payment.id, payment.reservation_id)

        else:

            payment.reject()
            self.repository.save(payment)

            event = FailedPayment(payment.reservation_id, "Funds insufficient")

        self.event_bus.publish_event(
            event.routing_key,
            event.type,
            event.to_dict()
        )

        return {
            "payment_id": payment.id,
            "state": payment.state,
            "event_generated": event.type
        }