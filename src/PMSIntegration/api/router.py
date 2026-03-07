from fastapi import APIRouter
from pydantic import BaseModel

from modules.pms.application.commands.confirm_reservation import ConfirmReservation
from modules.pms.application.commands.cancel_reservation import CancelReservation

router = APIRouter()


class ReservationRequest(BaseModel):
    id_reserva: str
    id_habitacion: str


class CancelRequest(BaseModel):
    id_reserva: str


@router.post("/confirmar-reserva")
def confirm_reservation(request: ReservationRequest):

    command = ConfirmReservation()

    return command.execute(
        request.id_reserva,
        request.id_habitacion
    )


@router.post("/cancelar-reserva")
def cancel_reservation(request: CancelRequest):

    command = CancelReservation()

    return command.execute(request.id_reserva)