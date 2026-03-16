from dataclasses import dataclass
import uuid
from Booking.seedwork.aplicacion.comandos import Comando

@dataclass
class CrearReservaHold(Comando):
    id_usuario: uuid.UUID
    id_habitacion: uuid.UUID
    monto: float
    fecha_reserva: str = None

@dataclass
class FormalizarReserva(Comando):
    id_reserva: uuid.UUID
    fecha_reserva: str = None

@dataclass
class ConfirmarReservaLocalCmd(Comando):
    id_reserva: uuid.UUID

@dataclass
class CancelarReservaLocalCmd(Comando):
    id_reserva: uuid.UUID
