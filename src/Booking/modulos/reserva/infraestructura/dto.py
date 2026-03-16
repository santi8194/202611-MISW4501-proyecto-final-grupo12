from Booking.config.db import db

class ReservaDTO(db.Model):
    __tablename__ = "reservas"
    id = db.Column(db.String(40), primary_key=True)
    id_usuario = db.Column(db.String(40), nullable=False)
    id_habitacion = db.Column(db.String(40), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha_reserva = db.Column(db.String(20), nullable=True)
    estado = db.Column(db.String(20), nullable=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False)
