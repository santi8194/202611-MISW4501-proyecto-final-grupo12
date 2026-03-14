from modules.payments.domain.events import PaymentRefundFailed, PaymentRefunded


class RefundPayment:

    def __init__(self, repository, event_bus):
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, reservation_id: str):

        payment = self.repository.obtain_by_reservation(reservation_id)

        if not payment:
            return {"error": "Payment not found"}
        
        if payment.state == "REFUNDED":
            event = PaymentRefundFailed(payment.id, payment.reservation_id)
            return {
                "message": "Payment was already refunded",
                "state": payment.state
            }

        payment.state = "REFUNDED"

        self.repository.save(payment)

        event = PaymentRefunded(payment.id, payment.reservation_id)

        self.event_bus.publish_event(
            event.routing_key,
            event.type,
            event.to_dict()
        )

        return {
            "reservation_id": payment.reservation_id,
            "payment_id": payment.id,
            "state": payment.state,
            "event_generated": event.type
        }