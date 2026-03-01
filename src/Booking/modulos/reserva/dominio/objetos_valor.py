from enum import Enum
from Booking.seedwork.dominio.objetos_valor import ObjetoValor
from dataclasses import dataclass

class EstadoReserva(Enum):
    HOLD = "HOLD"
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
