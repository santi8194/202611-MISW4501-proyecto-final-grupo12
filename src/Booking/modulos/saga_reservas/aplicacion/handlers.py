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
            monto=evento.monto,
            id_habitacion=evento.id_habitacion,
            fecha_reserva=evento.fecha_reserva
        )

class RespuestaSagaHandler(Handler):
    """
    Handler agnóstico que recibe cualquier evento proveniente de RabbitMQ (Pagos, PMS, etc.)
    y se lo entrega al Orquestador para que decida el siguiente paso.
    """
    def __init__(self, orquestador: OrquestadorSagaReservas):
        self.orquestador = orquestador

    def handle(self, evento):
        # En una app real, el evento hereda de una clase base p.ej EventoIntegracion con id_reserva
        if not hasattr(evento, 'id_reserva'):
            print("[RespuestaSagaHandler] Evento ignorado: No tiene id_reserva")
            return
            
        nombre_evento = evento.__class__.__name__
        print(f"\n[EVENTO RECIBIDO AGNOSTICO] {nombre_evento} detectado para: {evento.id_reserva}")
        
        # Convertimos el evento a diccionario para pasarlo como payload dinámico
        payload = vars(evento).copy()
        
        # Eliminamos id_reserva y campos base del framework para no mandarlos duplicados al unpacking de comandos
        claves_a_ignorar = ['id_reserva', 'id', 'fecha_creacion', 'correlacion_id']
        for k in claves_a_ignorar:
            if k in payload:
                del payload[k]
        
        self.orquestador.manejar_evento_respuesta(
            id_reserva=evento.id_reserva,
            evento_recibido=nombre_evento,
            payload_recibido=payload
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
