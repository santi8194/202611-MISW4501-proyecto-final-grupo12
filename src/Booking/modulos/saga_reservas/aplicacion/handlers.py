from Booking.seedwork.aplicacion.comandos import Handler
from Booking.modulos.reserva.dominio.eventos import ReservaPendiente
from Booking.modulos.saga_reservas.dominio.eventos import PagoExitosoEvt, ConfirmacionPmsExitosaEvt, RechazarReservaCmd
from Booking.modulos.saga_reservas.aplicacion.orquestador import OrquestadorSagaReservas

class IniciarSagaHandler(Handler):
    """
    Escucha el evento ReservaPendiente (generado cuando el usuario formaliza y paga)
    y detona el motor de la SAGA.
    """
    def __init__(self, orquestador: OrquestadorSagaReservas):
        self.orquestador = orquestador

    def handle(self, evento: ReservaPendiente):
        print(f"\n[EVENTO RECIBIDO] ReservaPendiente detectada para: {evento.id_reserva}")
        self.orquestador.iniciar_saga(
            id_reserva=evento.id_reserva,
            id_usuario=evento.id_usuario,
            monto=evento.monto
        )

class ContinuarSagaPagoHandler(Handler):
    def __init__(self, orquestador: OrquestadorSagaReservas):
        self.orquestador = orquestador

    def handle(self, evento: PagoExitosoEvt):
        print(f"\n[EVENTO RECIBIDO] PagoExitosoEvt detectado para: {evento.id_reserva}")
        # dummy room ID since event doesn't have it in this demo payload yet
        import uuid
        dummy_room = uuid.uuid4() 
        self.orquestador.manejar_pago_exitoso(
            id_reserva=evento.id_reserva,
            id_habitacion=dummy_room
        )

class FinalizarSagaPmsHandler(Handler):
    def __init__(self, orquestador: OrquestadorSagaReservas):
        self.orquestador = orquestador

    def handle(self, evento: ConfirmacionPmsExitosaEvt):
        print(f"\n[EVENTO RECIBIDO] ConfirmacionPmsExitosaEvt detectada para: {evento.id_reserva}")
        self.orquestador.manejar_confirmacion_pms(
            id_reserva=evento.id_reserva
        )

class CompensarSagaHandler(Handler):
    """
    Escucha un fallo crítico en la reserva (ej: Rechazo manual o timeout de pasarela de pagos)
    y detona la lógica de reserva de compensación LIFO.
    """
    def __init__(self, orquestador: OrquestadorSagaReservas):
        self.orquestador = orquestador

    def handle(self, comando: RechazarReservaCmd):
        print(f"\n[COMANDO RECIBIDO] RechazarReservaCmd detectado provocando un FALLO MASIVO LIFO.")
        self.orquestador.compensar_saga(
            id_reserva=comando.id_reserva,
            evento_fallo="RechazarReservaManualCmd"
        )
