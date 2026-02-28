from uuid import UUID
from modules.pms.application.services import PMSService
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/pms", tags=["PMS"])

service = PMSService()


class ReservationInput(BaseModel):
    booking_id: UUID
    hotel_id: str
    room_type: str
    guest_name: str


@router.post("/reserve")
def create_reservation(data: ReservationInput):
    try:
        reservation = service.create_reservation(
            booking_id=data.booking_id,
            hotel_id=data.hotel_id,
            room_type=data.room_type,
            guest_name=data.guest_name
        )
        return reservation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))