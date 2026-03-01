import uuid
from datetime import datetime

class Payment:
    def __init__(self, reservation_id: str, amount: float, currency: str):
        self.id = str(uuid.uuid4())
        self.reservation_id = reservation_id
        self.amount = amount
        self.currency = currency
        self.state = "PENDIENTE"
        self.created_at = datetime.utcnow()

    def approve(self):
        self.state = "APROBADO"

    def reject(self):
        self.state = "RECHAZADO"