from modules.pms.application.commands.confirm_reservation import ConfirmReservation
from modules.pms.application.commands.cancel_reservation import CancelReservation

from modules.pms.infrastructure.repository import ReservationRepository
from modules.pms.infrastructure.services.event_bus import EventBus


def handle_confirm_reservation(data):

    reservation_id = data["id_reserva"]
    room_id = data["id_habitacion"]
    fecha_reserva = data.get("fecha_reserva")

    print(f"[PMS] Command received: ConfirmReservation for reservation {reservation_id} on {fecha_reserva}")

    repository = ReservationRepository()
    event_bus = EventBus()

    use_case = ConfirmReservation(repository, event_bus)

    result = use_case.execute(reservation_id, room_id, fecha_reserva)

    print("[PMS] Result:", result)


def handle_cancel_reservation(data):

    reservation_id = data["id_reserva"]

    print(f"[PMS] Command received: CancelReservation for reservation {reservation_id}")

    repository = ReservationRepository()
    event_bus = EventBus()

    use_case = CancelReservation(repository, event_bus)

    result = use_case.execute(reservation_id)

    print("[PMS] Result:", result)