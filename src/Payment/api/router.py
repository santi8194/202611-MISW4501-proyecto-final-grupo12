from fastapi import APIRouter
from pydantic import BaseModel
from modules.payments.application.commands.process_payment import ProcessPayment
from modules.payments.application.commands.refund_payment import RefundPayment

router = APIRouter()

class PaymentRequest(BaseModel):
    reservation_id: str
    amount: float
    currency: str

class RefundRequest(BaseModel):
    payment_id: str

@router.post("/procesar_pago")
def procesar_pago(request: PaymentRequest):
    command = ProcessPayment()
    return command.execute(
        request.reservation_id,
        request.amount,
        request.currency
    )

@router.post("/reembolsar_pago")
def refund_payment(request: RefundRequest):
    command = RefundPayment()
    return command.execute(request.payment_id)