import logging

logger = logging.getLogger(__name__)

from Booking.config.db import db
from Booking.modulos.saga_reservas.infraestructura.dto import SagaDefinitionDTO, SagaStepsDefinitionDTO

def seed_saga_reservas():
    """
    Inicializar la configuración de la Saga si no existe.
    Esta configuración define el enrutamiento y los comandos/eventos de compensación.
    """
    if not db.session.query(SagaDefinitionDTO).filter_by(id_flujo="RESERVA_ESTANDAR").first():
        definicion = SagaDefinitionDTO(
            id_flujo="RESERVA_ESTANDAR", 
            version=1, 
            nombre_descriptivo="Flujo actual (Cobro -> Bloqueo PMS -> Revisión Manual)", 
            activo=True
        )
        db.session.add(definicion)

        pasos = [
            SagaStepsDefinitionDTO(index=0, id_flujo="RESERVA_ESTANDAR", version=1, comando="CrearReservaLocalCmd", evento="ReservaCreadaIntegracionEvt", error="ReservaCreadaFalloEvt", compensacion="CancelarReservaLocalCmd"),
            SagaStepsDefinitionDTO(index=1, id_flujo="RESERVA_ESTANDAR", version=1, comando="ProcesarPagoCmd", evento="PagoExitosoEvt", error="PagoRechazadoEvt", compensacion="ReversarPagoCmd"),
            SagaStepsDefinitionDTO(index=2, id_flujo="RESERVA_ESTANDAR", version=1, comando="ConfirmarReservaPmsCmd", evento="ConfirmacionPmsExitosaEvt", error="ReservaRechazadaPmsEvt", compensacion="CancelarReservaPmsCmd"),
            SagaStepsDefinitionDTO(index=3, id_flujo="RESERVA_ESTANDAR", version=1, comando="SolicitarAprobacionManualCmd", evento="ReservaAprobadaManualEvt", error="ReservaRechazadaManualEvt", compensacion=None),
            SagaStepsDefinitionDTO(index=4, id_flujo="RESERVA_ESTANDAR", version=1, comando="ConfirmarReservaLocalCmd", evento="ReservaConfirmadaEvt", error="FallaActualizacionLocalEvt", compensacion="CancelarReservaLocalCmd"),
            SagaStepsDefinitionDTO(index=5, id_flujo="RESERVA_ESTANDAR", version=1, comando="MarcarSagaEsperandoVoucher", evento="VoucherEnviadoEvt", error="FalloEnvioVoucherEvt", compensacion="NotificarFalloTecnicoCmd")
        ]
        db.session.add_all(pasos)
        db.session.commit()
        logger.info("[Booking API] Configuración de Saga Orquestada insertada en BD exitosamente.")
