import uuid
from typing import Optional
from Booking.seedwork.infraestructura.schema.v1.eventos import EventoIntegracion

class ReservaCreadaPayload:
    def __init__(self, id_reserva: str, id_cliente: str, estado: str, fecha_creacion: str, id_habitacion: Optional[str] = None, monto: Optional[float] = None, fecha_reserva: Optional[str] = None):
        self.id_reserva = id_reserva
        self.id_cliente = id_cliente
        self.estado = estado
        self.fecha_creacion = fecha_creacion
        self.id_habitacion = id_habitacion
        self.monto = monto
        self.fecha_reserva = fecha_reserva

    def to_dict(self):
        res = {
            "id_reserva": self.id_reserva,
            "id_cliente": self.id_cliente,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion
        }
        if self.id_habitacion is not None:
            res["id_habitacion"] = self.id_habitacion
        if self.monto is not None:
            res["monto"] = self.monto
        if self.fecha_reserva is not None:
            res["fecha_reserva"] = self.fecha_reserva
        return res

class EventoReservaCreada(EventoIntegracion):
    def __init__(self, data: ReservaCreadaPayload, id: str = None, time: str = None, ingestion: str = None, specversion: str = "v1", type: str = "ReservaCreada", datacontenttype: str = "application/json", service_name: str = "booking"):
        super().__init__()
        self.id = id or str(uuid.uuid4())
        self.time = time
        self.ingestion = ingestion
        self.specversion = specversion
        self.type = type
        self.datacontenttype = datacontenttype
        self.service_name = service_name
        self.data = data

    def to_dict(self):
        return {
            "id": self.id,
            "time": self.time,
            "ingestion": self.ingestion,
            "specversion": self.specversion,
            "type": self.type,
            "datacontenttype": self.datacontenttype,
            "service_name": self.service_name,
            "data": self.data.to_dict() if self.data else None
        }

class ReservaConfirmadaPayload:
    def __init__(self, id_reserva: str, emailCliente: str):
        self.id_reserva = id_reserva
        self.emailCliente = emailCliente

    def to_dict(self):
        return {
            "id_reserva": self.id_reserva,
            "emailCliente": self.emailCliente
        }

class EventoReservaConfirmada(EventoIntegracion):
    def __init__(self, data: ReservaConfirmadaPayload, id: str = None, time: str = None, ingestion: str = None, specversion: str = "v1", type: str = "ReservaConfirmadaEvt", datacontenttype: str = "application/json", service_name: str = "booking"):
        super().__init__()
        self.id = id or str(uuid.uuid4())
        self.time = time
        self.ingestion = ingestion
        self.specversion = specversion
        self.type = type
        self.datacontenttype = datacontenttype
        self.service_name = service_name
        self.data = data

    def to_dict(self):
        return {
            "id": self.id,
            "time": self.time,
            "ingestion": self.ingestion,
            "specversion": self.specversion,
            "type": self.type,
            "datacontenttype": self.datacontenttype,
            "service_name": self.service_name,
            "data": self.data.to_dict() if self.data else None
        }
