from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import PaymentModel

class PaymentRepository:

    def save(self, payment):
        db: Session = SessionLocal()

        model = PaymentModel(
            id=payment.id,
            reservation_id=payment.reservation_id,
            amount=payment.amount,
            currency=payment.currency,
            state=payment.state
        )

        db.merge(model)
        db.commit()
        db.close()

    def obtain_by_reservation(self, reservation_id):
        db: Session = SessionLocal()

        payment = db.query(PaymentModel)\
            .filter(PaymentModel.reservation_id == reservation_id)\
            .first()

        db.close()
        return payment

    def obtain_by_id(self, payment_id):
        db: Session = SessionLocal()

        payment = db.query(PaymentModel)\
            .filter(PaymentModel.id == payment_id)\
            .first()

        db.close()
        return payment