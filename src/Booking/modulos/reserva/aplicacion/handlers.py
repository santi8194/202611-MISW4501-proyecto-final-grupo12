from Booking.seedwork.aplicacion.comandos import Handler
from Booking.modulos.reserva.aplicacion.comandos import CrearReservaHold, FormalizarReserva
from Booking.modulos.reserva.dominio.entidades import Reserva
from Booking.modulos.reserva.infraestructura.repositorios import RepositorioReservas
from Booking.config.uow import UnidadTrabajoHibrida
import uuid

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
                monto=comando.monto
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
