from dataclasses import dataclass
import uuid
from Booking.seedwork.dominio.eventos import EventoDominio


# --- EVENTOS: Respuestas esperadas de otros microservicios ---
@dataclass
class PagoExitosoEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    token_pasarela: str = None

@dataclass
class PagoRechazadoEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    motivo: str = None

@dataclass
class ConfirmacionPmsExitosaEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    codigo_pms: str = None

@dataclass
class ReservaRechazadaPmsEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    motivo: str = None

@dataclass
class ReservaAprobadaManualEvt(EventoDominio):
    id_reserva: uuid.UUID = None

@dataclass
class ReservaRechazadaManualEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    motivo: str = None

@dataclass
class VoucherEnviadoEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    email: str = None
