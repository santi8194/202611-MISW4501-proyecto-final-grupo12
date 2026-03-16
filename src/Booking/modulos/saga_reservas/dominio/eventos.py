from dataclasses import dataclass
import uuid
from Booking.seedwork.aplicacion.comandos import Comando
from Booking.seedwork.dominio.eventos import EventoDominio

# --- COMANDOS: Acción Hacia Adelante ---
@dataclass
class ProcesarPagoCmd(Comando):
    id_reserva: uuid.UUID
    monto: float

@dataclass
class ConfirmarReservaPmsCmd(Comando):
    id_reserva: uuid.UUID
    id_habitacion: uuid.UUID
    fecha_reserva: str = None

# --- COMANDOS: Compensación (Rollback LIFO) ---
@dataclass
class CancelarReservaPmsCmd(Comando):
    id_reserva: uuid.UUID
    id_habitacion: uuid.UUID

@dataclass
class ReversarPagoCmd(Comando):
    id_reserva: uuid.UUID
    monto: float
    
@dataclass
class CancelarReservaLocalCmd(Comando):
    id_reserva: uuid.UUID

# --- EVENTOS: (Esperados de otros microservicios o internos) ---
@dataclass
class PagoExitosoEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    token_pasarela: str = None

@dataclass
class ConfirmacionPmsExitosaEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    codigo_pms: str = None
    
@dataclass
class ReservaRechazadaPmsEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    motivo: str = None

@dataclass
class SolicitarAprobacionManualCmd(Comando):
    id_reserva: uuid.UUID
    id_habitacion: uuid.UUID

@dataclass
class ReservaAprobadaManualEvt(EventoDominio):
    id_reserva: uuid.UUID = None

@dataclass
class ReservaRechazadaManualEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    motivo: str = None

@dataclass
class RechazarReservaCmd(Comando): # Detonante externo manual
    id_reserva: uuid.UUID = None

@dataclass
class MarcarSagaEsperandoVoucherCmd(Comando):
    id_reserva: uuid.UUID = None

@dataclass
class VoucherEnviadoEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    email: str = None
