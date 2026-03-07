from fastapi import APIRouter
from pydantic import BaseModel
from modules.payments.application.commands.process_payment import ProcessPayment
from modules.payments.application.commands.refund_payment import RefundPayment

router = APIRouter()

class PaymentRequest(BaseModel):
    id_reserva: str
    monto: float

class RefundRequest(BaseModel):
    id_pago: str

@router.post("/procesar_pago")
def procesar_pago(request: PaymentRequest):
    command = ProcessPayment()
    return command.execute(
        request.id_reserva,
        request.monto,
    )

@router.post("/reversar_pago")
def refund_payment(request: RefundRequest):
    command = RefundPayment()
    return command.execute(request.id_pago)