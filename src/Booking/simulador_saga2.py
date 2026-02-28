import uuid
import sys
import os


# Agregamos la ruta base para que Python encuentre el paquete 'Booking'
# Subimos un nivel desde simular_saga.py (src/Booking/) y apuntamos a src/

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Booking.api import create_app
from Booking.config.db import db
from Booking.modulos.reserva.aplicacion.comandos import CrearReservaHold, FormalizarReserva
from Booking.modulos.reserva.infraestructura.repositorios import RepositorioReservas
from Booking.config.uow import UnidadTrabajoHibrida

from Booking.modulos.saga_reservas.aplicacion.orquestador import OrquestadorSagaReservas
from Booking.modulos.saga_reservas.infraestructura.repositorios import RepositorioSagas
from Booking.modulos.reserva.dominio.eventos import ReservaPendiente
from Booking.modulos.saga_reservas.dominio.eventos import PagoExitosoEvt, ConfirmacionPmsExitosaEvt, RechazarReservaCmd
from Booking.modulos.saga_reservas.aplicacion.handlers import (
    IniciarSagaHandler, ContinuarSagaPagoHandler, 
    FinalizarSagaPmsHandler, CompensarSagaHandler
)

from Booking.modulos.saga_reservas.infraestructura.dto import (
    SagaDefinitionDTO, SagaStepsDefinitionDTO
)

# Monkey-patch para que el Despachador de RabbitMQ no intente conectarse (y falle) en esta prueba local sin BD/Broker real
from Booking.seedwork.infraestructura.dispatchers import DespachadorRabbitMQ
class MockDespachador:
    def publicar_evento(self, evento, routing_key): print(f" 🐇 [MOCK RABBITMQ PUBLISH] Evento: {routing_key}")
    def publicar_comando(self, comando, routing_key): print(f" 🐇 [MOCK RABBITMQ PUBLISH] Comando: {routing_key}")
    def cerrar(self): pass

DespachadorRabbitMQ.__new__ = lambda cls: MockDespachador()
# Fin de Mock

def run_simulation(happy_path=True):
    app = create_app()
    with app.app_context():
        # Limpiar BD en memoria
        db.drop_all()
        db.create_all()

        # Poblar configuración de la Saga
        definicion = SagaDefinitionDTO(
            id_flujo="RESERVA_ESTANDAR", 
            version=1, 
            nombre_descriptivo="Flujo actual (Cobro -> Bloqueo PMS -> Revisión Manual)", 
            activo=True
        )
        db.session.add(definicion)

        # Poblar pasos (Routing Slip)
        pasos = [
            # PASO 1: Cobrar al cliente
            SagaStepsDefinitionDTO(
                index=1, 
                id_flujo="RESERVA_ESTANDAR", 
                version=1, 
                comando="ProcesarPagoCmd", 
                evento="PagoExitosoEvt", 
                error="PagoRechazadoEvt", 
                compensacion="ReversarPagoCmd"
            ),
            # PASO 2: Confirmar disponibilidad con el Hotel (MS de PMS)
            SagaStepsDefinitionDTO(
                index=2, 
                id_flujo="RESERVA_ESTANDAR", 
                version=1, 
                comando="ConfirmarReservaPmsCmd", 
                evento="ConfirmacionPmsExitosaEvt", 
                error="ReservaRechazadaPmsEvt", 
                compensacion="CancelarReservaPmsCmd"
            ),
            # PASO 3: Aprobación manual del Backoffice o Admin
            SagaStepsDefinitionDTO(
                index=3, 
                id_flujo="RESERVA_ESTANDAR", 
                version=1, 
                comando="SolicitarAprobacionManualCmd", 
                evento="ReservaAprobadaManualEvt", 
                error="ReservaRechazadaManualEvt", 
                compensacion=None
            ),
            # PASO 4: Confirmación definitiva local (Sincroniza la BD de Reservas)
            SagaStepsDefinitionDTO(
                index=4, 
                id_flujo="RESERVA_ESTANDAR", 
                version=1, 
                comando="ConfirmarReservaLocalCmd", 
                evento="ReservaConfirmadaLocalEvt", 
                error="FallaActualizacionLocalEvt", 
                compensacion="CancelarReservaLocalCmd"
            ),
            # PASO 5: Cierre por Coreografía (El Notificador hace su trabajo)
            SagaStepsDefinitionDTO(
                index=5, 
                id_flujo="RESERVA_ESTANDAR", 
                version=1, 
                comando="MarcarSagaEsperandoVoucher", # Marcador interno del ORQ
                evento="VoucherEnviadoEvt", 
                error="FalloEnvioVoucherEvt", 
                compensacion="NotificarFalloTecnicoCmd"
            )
        ]
        db.session.add_all(pasos)
        db.session.commit()
        print("[Simulación] Definición de Saga persitida en BD en memoria.")
        
        print("\n=======================================================")
        print(f"🚀 INICIANDO SIMULACIÓN DE LA SAGA ({'CAMINO FELIZ' if happy_path else 'FALLO Y COMPENSACIÓN'})")
        print("=======================================================\n")

        # IDs de prueba
        id_user = uuid.uuid4()
        id_room = uuid.uuid4()
        monto = 1500.0

        # MÓDULO RESERVA (Vía API Rest API - Test Client)
        client = app.test_client()
        
        # 1. Crear Reserva HOLD vía API
        print("--- 1. USUARIO CREA RESERVA EN ESTADO HOLD (15 Minutos) [Vía HTTP POST /api/reserva] ---")
        payload_crear = {
            "id_usuario": str(id_user),
            "id_habitacion": str(id_room),
            "monto": monto
        }
        response_crear = client.post('/api/reserva', json=payload_crear)
        
        if response_crear.status_code != 201:
            print(f"Error creando reserva: {response_crear.get_json()}")
            return
            
        reserva_data = response_crear.get_json()
        id_reserva_str = reserva_data.get('id_reserva')
        id_reserva = uuid.UUID(id_reserva_str)
        print(f"Respuesta API: {reserva_data}")
        
        # 2. Formalizar Reserva vía API
        print("\n--- 2. USUARIO FORMALIZA Y PAGA LA RESERVA [Vía HTTP POST /api/reserva/<id>/formalizar] ---")
        response_formalizar = client.post(f'/api/reserva/{id_reserva_str}/formalizar')
        
        if response_formalizar.status_code != 200:
            print(f"Error formalizando reserva: {response_formalizar.get_json()}")
            return
            
        print(f"Respuesta API: {response_formalizar.get_json()}")
        
        # SIMULACIÓN DEL MOTOR DE SAGA
        repo_sagas = RepositorioSagas()
        uow = UnidadTrabajoHibrida()
        orquestador = OrquestadorSagaReservas(repo_sagas, uow)
        
        print("\n--- 3. MOTOR DE SAGA DETECTA RESERVA_PENDIENTE Y ARRANCA ---")
        handler_inicio_saga = IniciarSagaHandler(orquestador)
        # La API formaliza pero no podemos enlazar RabbitMQ en esta simple prueba sincrónica 
        # sin levantar Workers, así que inyectamos el pulso inicial que normalmente 
        # llegaría por la cola de mensajes al Orquestador.
        handler_inicio_saga.handle(ReservaPendiente(id_reserva=id_reserva, id_usuario=id_user, monto=monto))

        print("\n--- 4. SIMULANDO RESPUESTA DEL MICROSERVICIO DE PAGOS ---")
        if happy_path:
            handler_pago = ContinuarSagaPagoHandler(orquestador)
            handler_pago.handle(PagoExitosoEvt(id_reserva=id_reserva, token_pasarela="token_ab123"))

            print("\n--- 5. SIMULANDO RESPUESTA DEL PMS (HOTEL) ---")
            handler_pms = FinalizarSagaPmsHandler(orquestador)
            handler_pms.handle(ConfirmacionPmsExitosaEvt(id_reserva=id_reserva, codigo_pms="HTL-999"))
            
            print("\n🎉 SIMULACIÓN EXITOSA COMPLETADA 🎉\n")
        
        else:
            print("\n🚨 [ALERTA] EL MICROSERVICIO DE PAGOS/CANTIDAD REPORTÓ UN FALLO CRÍTICO 🚨")
            handler_fallo = CompensarSagaHandler(orquestador)
            handler_fallo.handle(RechazarReservaCmd(id_reserva=id_reserva))
            
            print("\n🛑 SIMULACIÓN DE COMPENSACIÓN COMPLETADA 🛑\n")

if __name__ == "__main__":
    print("Ejecutando Camino Exitoso...")
    run_simulation(happy_path=True)
    
    print("\n\n" + "*"*80 + "\n\n")
    
    print("Ejecutando Camino de Fallo (Compensación LIFO)...")
    run_simulation(happy_path=False)
