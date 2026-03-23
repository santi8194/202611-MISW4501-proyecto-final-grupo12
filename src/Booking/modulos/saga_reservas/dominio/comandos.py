from dataclasses import dataclass
import uuid
from Booking.seedwork.aplicacion.comandos import Comando


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

@dataclass
class SolicitarAprobacionManualCmd(Comando):
    id_reserva: uuid.UUID
    id_habitacion: uuid.UUID

@dataclass
class MarcarSagaEsperandoVoucherCmd(Comando):
    id_reserva: uuid.UUID = None


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
class RechazarReservaCmd(Comando):  # Detonante externo manual
    id_reserva: uuid.UUID = None
