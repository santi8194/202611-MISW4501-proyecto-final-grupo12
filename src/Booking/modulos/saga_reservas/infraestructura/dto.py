from Booking.config.db import db

class SagaInstanceDTO(db.Model):
    __tablename__ = "saga_instances"
    
    id = db.Column(db.String(40), primary_key=True)
    id_reserva = db.Column(db.String(40), nullable=False)
    id_flujo = db.Column(db.String(50), nullable=False)
    version_ejecucion = db.Column(db.Integer, nullable=False, default=1)
    estado_global = db.Column(db.String(30), nullable=False)
    paso_actual = db.Column(db.Integer, nullable=False, default=0)
    fecha_creacion = db.Column(db.DateTime, nullable=False)
    ultima_actualizacion = db.Column(db.DateTime, nullable=False)
    
    # Relación uno a muchos con el log de ejecución
    historial = db.relationship('SagaExecutionLogDTO', backref='saga_instance', lazy=True, cascade="all, delete-orphan")

class SagaExecutionLogDTO(db.Model):
    __tablename__ = "saga_execution_logs"
    
    id = db.Column(db.String(40), primary_key=True)
    id_instancia = db.Column(db.String(40), db.ForeignKey('saga_instances.id'), nullable=False)
    tipo_mensaje = db.Column(db.String(30), nullable=False)
    accion = db.Column(db.String(100), nullable=False)
    
    # JSONB es ideal en postgres, pero usamos Text o JSON para SQLite/MySQL genérico en este esqueleto
    payload_snapshot = db.Column(db.JSON, nullable=True) 
    
    fecha_registro = db.Column(db.DateTime, nullable=False)
