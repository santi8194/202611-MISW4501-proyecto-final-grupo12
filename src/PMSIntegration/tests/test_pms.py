from uuid import uuid4
from modules.pms.application.services import PMSService


def test_create_reservation():
    service = PMSService()

    result = service.create_reservation(
        reservation_id=uuid4(),
        hotel_id="HTL001",
        room_type="DOBLE",
        guest_name="Mariana Diaz"
    )

    assert result["state"] == "CONFIRMED"


def test_confirm_reservation_success():
    from modules.pms.application.commands.confirm_reservation import ConfirmReservation
    from modules.pms.infrastructure.repository import ReservationRepository
    from modules.shared.infrastructure.event_bus import MockEventBus

    reservation_id = "026b1992-7b50-49f3-9f7e-0e30663543c3"
    room_id = "550e8400-e29b-41d4-a716-446655440000"
    fecha_reserva = "2026-03-14"

    repository = ReservationRepository()
    event_bus = MockEventBus()
    use_case = ConfirmReservation(repository, event_bus)

    result = use_case.execute(reservation_id, room_id, fecha_reserva)

    assert result is not None
    assert result["event_generated"] == "ConfirmacionPmsExitosaEvt"