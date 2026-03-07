from modules.pms.application.commands.confirm_reservation import ConfirmReservation
from modules.pms.application.commands.cancel_reservation import CancelReservation

from modules.pms.infrastructure.repository import ReservationRepository
from modules.pms.infrastructure.services.event_bus import EventBus


def handle_confirm_reservation(data):

    booking_id = data["booking_id"]

    print(f"[PMS] Command received: ConfirmReservation for booking {booking_id}")

    repository = ReservationRepository()
    event_bus = EventBus()

    use_case = ConfirmReservation(repository, event_bus)

    result = use_case.execute(booking_id)

    print("[PMS] Result:", result)


def handle_cancel_reservation(data):

    booking_id = data["booking_id"]

    print(f"[PMS] Command received: CancelReservation for booking {booking_id}")

    repository = ReservationRepository()
    event_bus = EventBus()

    use_case = CancelReservation(repository, event_bus)

    result = use_case.execute(booking_id)

    print("[PMS] Result:", result)