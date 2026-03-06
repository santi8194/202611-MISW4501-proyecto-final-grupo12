from typing import List
from Booking.seedwork.aplicacion.uow import UnidadTrabajo
from Booking.config.db import db
from Booking.seedwork.infraestructura.dispatchers import DespachadorRabbitMQ
from Booking.seedwork.aplicacion.dispatchers import Despachador
from Booking.modulos.reserva.infraestructura.mapeadores import MapeadorEventosReserva

class UnidadTrabajoHibrida(UnidadTrabajo):
    """
    Coordina la persistencia en la base de datos (SQLAlchemy) con el envío 
    de eventos de dominio hacia el bus de mensajes (RabbitMQ).
    Garantiza que los eventos solo se publiquen si la transacción en BD fue exitosa.
    """

    def __init__(self, despachador: Despachador = None):
        self._eventos: List = []
        # Inyectamos el despachador por dependencias, usando RabbitMQ por defecto si no se provee.
        self._despachador = despachador or DespachadorRabbitMQ(mapeador_eventos=MapeadorEventosReserva())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.rollback()
        self._despachador.cerrar()

    def agregar_eventos(self, eventos: List):
        self._eventos.extend(eventos)

    def commit(self):
        try:
            # 1. Commit en la base de datos (SQLAlchemy)
            db.session.commit()
            
            # 2. Si el commit falla, lanzará una excepción y NUNCA llegaremos aquí.
            for evento in self._eventos:
                try:
                    # Distinguimos si es un Comando o un Evento
                    clase_nombre = evento.__class__.__name__
                    if "Cmd" in clase_nombre or "EsperandoVoucher" in clase_nombre:
                         # Es un comando, llamamos a publicar_comando delegando la key al dispatcher
                         # ya que el dispatcher internamente la deduce por el tipo
                         # Por ahora llamamos sin routing key (esto fallará si el dispatcher requiere obligatoriamente un key puro)
                         # Pero en dispatchers.py vimos que publicarlo a traves de evento_integracion como si fuera evento resuelve su key
                         # HACK: Pasarlo por publicar_evento así el dispatcher de RMQ hace el enrutamiento. 
                         # Lo ideal sería que publicar_comando resolviera la key o UoW se la pasara.
                         print(f"[UoW] Publicando comando: {clase_nombre}", flush=True)
                         self._despachador.publicar_evento(evento, 'travelhub.commands.exchange')
                    else:
                         print(f"[UoW] Publicando evento de dominio: {clase_nombre}", flush=True)
                         self._despachador.publicar_evento(evento, 'eventos_dominio')
                except Exception as e:
                    print(f"Error publicando evento: {e}", flush=True)
            # Limpiamos los eventos despachados después de intentar publicarlos
            self._eventos.clear()

        except Exception as e:
            self.rollback()
            raise Exception(f"Fallo en la Unidad de Trabajo: {str(e)}")

    def rollback(self):
        db.session.rollback()
        self._eventos.clear()
