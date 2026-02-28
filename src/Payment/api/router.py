from fastapi import APIRouter
from pydantic import BaseModel
from modules.payments.application.commands.process_payment import ProcessPayment

router = APIRouter()

class PaymentRequest(BaseModel):
    reservation_id: str
    amount: float
    currency: str

@router.post("/process-payment")
def procesar_pago(request: PaymentRequest):
    comando = ProcessPayment()
    return comando.execute(
        request.reservation_id,
        request.amount,
        request.currency
    )