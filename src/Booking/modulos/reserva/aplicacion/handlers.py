from Booking.seedwork.aplicacion.comandos import Handler
from Booking.modulos.reserva.aplicacion.comandos import (
    CrearReservaHold, FormalizarReserva, 
    ConfirmarReservaLocalCmd, CancelarReservaLocalCmd
)
from Booking.modulos.reserva.dominio.entidades import Reserva
from Booking.modulos.reserva.dominio.eventos import (
    ReservaConfirmadaEvt, FallaActualizacionLocalEvt
)
from Booking.modulos.reserva.infraestructura.repositorios import RepositorioReservas
from Booking.config.uow import UnidadTrabajoHibrida
import uuid
from datetime import datetime

class CrearReservaHoldHandler(Handler):
    def __init__(self, repositorio: RepositorioReservas, uow: UnidadTrabajoHibrida):
        self.repositorio = repositorio
        self.uow = uow
    
    def handle(self, comando: CrearReservaHold) -> uuid.UUID:
        with self.uow:
            reserva = Reserva(id=uuid.uuid4())
            reserva.iniciar_reserva_hold(
                id_usuario=comando.id_usuario,
                id_habitacion=comando.id_habitacion,
                monto=comando.monto,
                fecha_reserva=comando.fecha_reserva
            )
            
            self.uow.agregar_eventos(reserva.eventos)
            self.repositorio.agregar(reserva)
            
            # Trigger UoW Híbrida (Salva en BD -> Publica eventos a RabbitMQ)
            self.uow.commit() 
            print(f"Reserva_Hold persistida y evento despachado: {reserva.id}")
        return reserva.id

class FormalizarReservaHandler(Handler):
    def __init__(self, repositorio: RepositorioReservas, uow: UnidadTrabajoHibrida):
        self.repositorio = repositorio
        self.uow = uow
    
    def handle(self, comando: FormalizarReserva) -> bool:
        with self.uow:
            reserva: Reserva = self.repositorio.obtener_por_id(str(comando.id_reserva))
            if not reserva:
                raise ValueError(f"No se encontró la reserva con ID: {comando.id_reserva}")
            
            reserva.formalizar_y_pagar()
            
            self.uow.agregar_eventos(reserva.eventos)
            self.repositorio.actualizar(reserva)
            
            # La UoW inserta en BD y publica el ReservaPendienteEvt
            self.uow.commit() 
            print(f"Reserva {reserva.id} formalizada (PENDIENTE) y evento despachado.")
        return True

class ConfirmarReservaLocalHandler(Handler):
    def __init__(self, repositorio: RepositorioReservas, uow: UnidadTrabajoHibrida):
        self.repositorio = repositorio
        self.uow = uow
    
    def handle(self, comando: ConfirmarReservaLocalCmd) -> ReservaConfirmadaEvt:
        with self.uow:
            reserva: Reserva = self.repositorio.obtener_por_id(str(comando.id_reserva))
            if not reserva:
                raise ValueError(f"No se encontró la reserva con ID: {comando.id_reserva}")
            
            # Usar la lógica de dominio
            reserva.confirmar_reserva()
            
            # Limpiamos los eventos genéricos y en su lugar anexamos nuestro evento de ruteo local.
            reserva.eventos.clear() 
            evento_local = ReservaConfirmadaEvt(
                id_reserva=reserva.id, 
                fecha_actualizacion=datetime.now()
            )
            reserva.agregar_evento(evento_local)
            
            self.uow.agregar_eventos(reserva.eventos)
            self.repositorio.actualizar(reserva)
            self.uow.commit() 
            print(f"✅ [HANDLER LOCAL] Reserva {reserva.id} CONFIRMADA localmente.")
        return evento_local

class CancelarReservaLocalHandler(Handler):
    def __init__(self, repositorio: RepositorioReservas, uow: UnidadTrabajoHibrida):
        self.repositorio = repositorio
        self.uow = uow
    
    def handle(self, comando: CancelarReservaLocalCmd) -> FallaActualizacionLocalEvt:
        with self.uow:
            reserva: Reserva = self.repositorio.obtener_por_id(str(comando.id_reserva))
            if not reserva:
                raise ValueError(f"No se encontró la reserva con ID: {comando.id_reserva}")
            
            # Lógica de dominio para cancelar
            reserva.cancelar_reserva()
            
            reserva.eventos.clear()
            evento_falla = FallaActualizacionLocalEvt(
                id_reserva=reserva.id, 
                fecha_actualizacion=datetime.now()
            )
            reserva.agregar_evento(evento_falla)
            
            self.uow.agregar_eventos(reserva.eventos)
            self.repositorio.actualizar(reserva)
            self.uow.commit() 
            print(f"❌ [HANDLER LOCAL] Reserva {reserva.id} CANCELADA localmente por compensación.")
        return evento_falla
