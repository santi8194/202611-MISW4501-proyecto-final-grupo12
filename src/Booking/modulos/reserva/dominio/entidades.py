from __future__ import annotations
from dataclasses import dataclass, field
import datetime
import uuid

from Booking.seedwork.dominio.entidades import AgregacionRaiz
from Booking.modulos.reserva.dominio.objetos_valor import EstadoReserva
from Booking.modulos.reserva.dominio.eventos import (
    ReservaIniciada,
    ReservaPendiente,
    ReservaConfirmada,
    ReservaCancelada
)

@dataclass
class Reserva(AgregacionRaiz):
    id_usuario: uuid.UUID = field(default=None)
    id_habitacion: uuid.UUID = field(default=None)
    monto: float = field(default=0.0)
    fecha_reserva: str = field(default=None)
    estado: EstadoReserva = field(default=EstadoReserva.HOLD)
    fecha_creacion: datetime.datetime = field(default_factory=datetime.datetime.now)
    fecha_actualizacion: datetime.datetime = field(default_factory=datetime.datetime.now)

    def iniciar_reserva_hold(self, id_usuario: uuid.UUID, id_habitacion: uuid.UUID, monto: float, fecha_reserva: str = None):
        self.id_usuario = id_usuario
        self.id_habitacion = id_habitacion
        self.monto = monto
        self.fecha_reserva = fecha_reserva
        self.estado = EstadoReserva.HOLD
        self.fecha_creacion = datetime.datetime.now()
        self.fecha_actualizacion = self.fecha_creacion

        # Emitimos un evento interno de dominio que la reserva se inició en HOLD.
        self.agregar_evento(ReservaIniciada(
            id_reserva=self.id,
            id_usuario=self.id_usuario,
            id_habitacion=self.id_habitacion,
            monto=self.monto,
            fecha_reserva=self.fecha_reserva,
            fecha_creacion=self.fecha_creacion
        ))

    def formalizar_y_pagar(self):
        # Valida que la reserva esté en HOLD antes de proceder
        if self.estado != EstadoReserva.HOLD:
            raise ValueError("La reserva debe estar en estado HOLD para ser formalizada")

        # Verifica tiempo de expiración (15 minutos)
        tiempo_transcurrido = datetime.datetime.now() - self.fecha_creacion
        if tiempo_transcurrido.total_seconds() > 900: # 15 minutos * 60 segundos
            self.estado = EstadoReserva.CANCELADA
            self.fecha_actualizacion = datetime.datetime.now()
            self.agregar_evento(ReservaCancelada(
                id_reserva=self.id,
                fecha_actualizacion=self.fecha_actualizacion
            ))
            raise ValueError("El tiempo de bloqueo (15 minutos) ha expirado")

        self.estado = EstadoReserva.PENDIENTE
        self.fecha_actualizacion = datetime.datetime.now()
        
        # Este evento actuará como detonante para el módulo SAGA
        self.agregar_evento(ReservaPendiente(
            id_reserva=self.id,
            id_usuario=self.id_usuario,
            id_habitacion=self.id_habitacion,
            monto=self.monto,
            fecha_reserva=self.fecha_reserva
        ))

    def confirmar_reserva(self):
        if self.estado != EstadoReserva.PENDIENTE:
             raise ValueError("La reserva debe estar en PENDIENTE para ser confirmada")
             
        self.estado = EstadoReserva.CONFIRMADA
        self.fecha_actualizacion = datetime.datetime.now()
        self.agregar_evento(ReservaConfirmada(
            id_reserva=self.id,
            fecha_actualizacion=self.fecha_actualizacion
        ))

    def cancelar_reserva(self):
        self.estado = EstadoReserva.CANCELADA
        self.fecha_actualizacion = datetime.datetime.now()
        self.agregar_evento(ReservaCancelada(
            id_reserva=self.id,
            fecha_actualizacion=self.fecha_actualizacion
        ))
