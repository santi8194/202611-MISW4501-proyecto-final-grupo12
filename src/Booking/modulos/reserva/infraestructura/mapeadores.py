from Booking.seedwork.dominio.repositorios import Mapeador
from Booking.seedwork.dominio.eventos import EventoDominio
from Booking.modulos.reserva.dominio.eventos import ReservaPendiente
from .schema.v1.eventos import EventoReservaCreada, ReservaCreadaPayload
import datetime

class MapeadorEventosReserva(Mapeador):

    versions = ('v1',)
    LATEST_VERSION = versions[0]

    def __init__(self):
        self.router = {
            ReservaPendiente: self._entidad_a_reserva_creada
        }

    def obtener_tipo(self) -> type:
        return EventoDominio.__class__

    def es_version_valida(self, version):
        for v in self.versions:
            if v == version:
                return True
        return False

    def _entidad_a_reserva_creada(self, evento: ReservaPendiente, version=LATEST_VERSION):
        def v1(ev):
            payload = ReservaCreadaPayload(
                id_reserva=str(ev.id_reserva),
                id_cliente=str(ev.id_cliente),
                estado="PENDIENTE",
                fecha_creacion=ev.fecha_evento.isoformat() if hasattr(ev, 'fecha_evento') else datetime.datetime.now().isoformat()
            )
            evento_integracion = EventoReservaCreada(
                id=str(ev.id),
                time=datetime.datetime.now().isoformat(),
                specversion=str(version),
                type='ReservaCreadaIntegracionEvt',
                data=payload
            )
            return evento_integracion

        if not self.es_version_valida(version):
            raise Exception(f'No se sabe procesar la version {version}')

        if version == 'v1':
            return v1(evento)

    def entidad_a_dto(self, entidad: EventoDominio, version=LATEST_VERSION):
        if not entidad:
            raise Exception("Evento nulo")
        
        func = self.router.get(entidad.__class__, None)
        if not func:
            print(f"[Mapeador] ADVERTENCIA: No existe implementación para el evento de dominio {entidad.__class__.__name__}. Se retornará nulo.")
            return None

        return func(entidad, version=version)

    def dto_a_entidad(self, dto, version=LATEST_VERSION):
        raise NotImplementedError
