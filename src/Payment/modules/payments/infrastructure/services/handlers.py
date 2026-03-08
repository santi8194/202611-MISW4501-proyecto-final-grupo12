from modules.payments.application.commands.process_payment import ProcessPayment
from modules.payments.application.commands.refund_payment import RefundPayment
from modules.payments.infrastructure.repository import PaymentRepository
from modules.payments.infrastructure.services.event_bus import EventBus

def handle_process_payment(data):

    reservation_id = data["id_reserva"]
    amount = data["monto"]

    print(f"[PAYMENTS] Command received: ProcessPayment for reservation {reservation_id}")

    repository = PaymentRepository()
    event_bus = EventBus()

    use_case = ProcessPayment(repository, event_bus)

    result = use_case.execute(
        reservation_id,
        amount,
    )

    print("[PAYMENTS] Result:", result)


def handle_refund_payment(data):

    reservation_id = data["id_reserva"]

    print(f"[PAYMENTS] Command received: RefundPayment for reservation {reservation_id}")

    repository = PaymentRepository()
    event_bus = EventBus()

    use_case = RefundPayment(repository, event_bus)

    result = use_case.execute(reservation_id)

    print("[PAYMENTS] Result:", result)