from fastapi import APIRouter
from pydantic import BaseModel
from modules.pms.infrastructure.repository import ReservationRepository
from modules.pms.infrastructure.services.event_bus import EventBus
from modules.pms.application.commands.confirm_reservation import ConfirmReservation
from modules.pms.application.commands.cancel_reservation import CancelReservation

router = APIRouter()
repository = ReservationRepository()
event_bus = EventBus()


class ReservationRequest(BaseModel):
    id_reserva: str
    id_habitacion: str


class CancelRequest(BaseModel):
    id_reserva: str


@router.post("/confirmar-reserva")
def confirm_reservation(request: ReservationRequest):

    command = ConfirmReservation(repository, event_bus)

    return command.execute(
        request.id_reserva,
        request.id_habitacion
    )


@router.post("/cancelar-reserva")
def cancel_reservation(request: CancelRequest):

    command = CancelReservation(repository, event_bus)

    return command.execute(request.id_reserva)


@router.get("/health")
def health():
    return {"status": "Pmsintegration Service running"}