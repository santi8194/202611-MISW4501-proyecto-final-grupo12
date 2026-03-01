from modules.payments.domain.events import PaymentRefunded
from modules.payments.infrastructure.repository import PaymentRepository
from modules.payments.infrastructure.event_bus import EventBus

repository = PaymentRepository()
event_bus = EventBus()

class RefundPayment:

    def execute(self, payment_id: str):

        payment = repository.obtain_by_id(payment_id)

        if not payment:
            return {"error": "Payment not found"}

        payment.state = "REFUNDED"
        repository.save(payment)
        event = PaymentRefunded(payment.id, payment.reservation_id)
        event_bus.publish(event.type, event.to_dict())
        
        return {
            "payment_id": payment.id,
            "state": payment.state
        }