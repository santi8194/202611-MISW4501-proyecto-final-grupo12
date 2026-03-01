from fastapi import APIRouter
from pydantic import BaseModel

from modules.pms.application.commands.confirm_reservation import ConfirmReservation
from modules.pms.application.commands.cancel_reservation import CancelReservation

router = APIRouter()


class ReservationRequest(BaseModel):
    booking_id: str
    hotel_id: str
    room_type: str
    guest_name: str


class CancelRequest(BaseModel):
    reservation_id: str


@router.post("/confirm-reservation")
def confirm_reservation(request: ReservationRequest):

    command = ConfirmReservation()

    return command.execute(
        request.booking_id,
        request.hotel_id,
        request.room_type,
        request.guest_name
    )


@router.post("/cancel-reservation")
def cancel_reservation(request: CancelRequest):

    command = CancelReservation()

    return command.execute(request.reservation_id)