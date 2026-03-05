from typing import List
from Booking.seedwork.aplicacion.uow import UnidadTrabajo
from Booking.config.db import db
from Booking.seedwork.infraestructura.dispatchers import DespachadorRabbitMQ
from Booking.seedwork.aplicacion.dispatchers import Despachador

class UnidadTrabajoHibrida(UnidadTrabajo):
    """
    Coordina la persistencia en la base de datos (SQLAlchemy) con el envío 
    de eventos de dominio hacia el bus de mensajes (RabbitMQ).
    Garantiza que los eventos solo se publiquen si la transacción en BD fue exitosa.
    """

    def __init__(self, despachador: Despachador = None):
        self._eventos: List = []
        # Inyectamos el despachador por dependencias, usando RabbitMQ por defecto si no se provee.
        self._despachador = despachador or DespachadorRabbitMQ()

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
            for evento in self._eventos: # Assuming db_eventos should be self._eventos
                try:
                    # Dejamos que el despachador se encargue de mapear el Evento de Dominio a Integración
                    self._despachador.publicar_evento(evento, 'eventos_dominio')
                except Exception as e:
                    print(f"Error publicando evento: {e}")
            # Limpiamos los eventos despachados después de intentar publicarlos
            self._eventos.clear()

        except Exception as e:
            self.rollback()
            raise Exception(f"Fallo en la Unidad de Trabajo: {str(e)}")

    def rollback(self):
        db.session.rollback()
        self._eventos.clear()
