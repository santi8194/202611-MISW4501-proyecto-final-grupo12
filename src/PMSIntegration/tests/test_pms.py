from uuid import uuid4
from modules.pms.application.services import PMSService


def test_create_reservation():
    service = PMSService()

    result = service.create_reservation(
        booking_id=uuid4(),
        hotel_id="HTL001",
        room_type="DOBLE",
        guest_name="Mariana Diaz"
    )

    assert result["state"] == "CONFIRMED"