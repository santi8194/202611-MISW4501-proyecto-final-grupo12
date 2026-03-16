from __future__ import annotations
from dataclasses import dataclass, field
import uuid
from datetime import datetime

from Booking.seedwork.dominio.eventos import EventoDominio

@dataclass
class ReservaIniciada(EventoDominio):
    id_reserva: uuid.UUID = None
    id_usuario: uuid.UUID = None
    id_habitacion: uuid.UUID = None
    monto: float = None
    fecha_reserva: str = None
    fecha_creacion: datetime = None

@dataclass
class ReservaPendiente(EventoDominio):
    id_reserva: uuid.UUID = None
    id_usuario: uuid.UUID = None
    id_habitacion: uuid.UUID = None
    monto: float = None
    fecha_reserva: str = None

@dataclass
class ReservaConfirmada(EventoDominio):
    id_reserva: uuid.UUID = None
    fecha_actualizacion: datetime = None

@dataclass
class ReservaCancelada(EventoDominio):
    id_reserva: uuid.UUID = None
    fecha_actualizacion: datetime = None

@dataclass
class ReservaConfirmadaEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    fecha_actualizacion: datetime = None

@dataclass
class FallaActualizacionLocalEvt(EventoDominio):
    id_reserva: uuid.UUID = None
    fecha_actualizacion: datetime = None
