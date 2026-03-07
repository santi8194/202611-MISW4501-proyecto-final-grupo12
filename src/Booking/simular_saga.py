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
    IniciarSagaHandler, RespuestaSagaHandler, CompensarSagaHandler
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

DespachadorRabbitMQ.__new__ = lambda cls, *args, **kwargs: MockDespachador()
# Fin de Mock

def run_simulation(app, init_db=True, happy_path=True):
    with app.app_context():
        if init_db:
            # La definición de la Saga y las tablas ya se crearon en Booking/api/__init__.py
            # al hacer app = create_app(). Simplemente notificamos aquí.
            print("[Simulación] Usando definición de Saga desde la inicialización de la API (Booking/api/__init__.py).\n")
        
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
            handler_respuesta = RespuestaSagaHandler(orquestador)
            # En una arquitectura madura este evento de integracion puede venir con metadata ampliada, pero ahora simulamos la firma exacta
            handler_respuesta.handle(PagoExitosoEvt(id_reserva=id_reserva, token_pasarela="token_ab123"))

            print("\n--- 5. SIMULANDO RESPUESTA DEL PMS (HOTEL) ---")
            handler_respuesta.handle(ConfirmacionPmsExitosaEvt(id_reserva=id_reserva, codigo_pms="HTL-999"))
            
            print("\n--- 6. SIMULANDO APROBACIÓN MANUAL ---")
            from Booking.modulos.saga_reservas.dominio.eventos import ReservaAprobadaManualEvt
            
            # Nota: Necesitamos un handler genérico en orquestador o crearlo rátpido
            # Para esta demostración de orquestador, podemos hacer orquestador.manejar_aprobacion(id_reserva)
            # o simplemente enviar el Evento si existe el Handler
            
            # Como Orquestador es un patron router, vamos a enrutar la Aprobación
            orquestador.manejar_evento_respuesta(id_reserva, "ReservaAprobadaManualEvt", {"status": "aprobado"})
            
            print("\n--- 7. SIMULANDO ENVÍO DE VOUCHER POR COREOGRAFÍA ---")
            from Booking.modulos.saga_reservas.dominio.eventos import VoucherEnviadoEvt
            handler_respuesta.handle(VoucherEnviadoEvt(id_reserva=id_reserva, email="cliente@dummy.com"))
            
            print("\n🎉 SIMULACIÓN EXITOSA COMPLETADA 🎉\n")
        
        else:
            print("\n🚨 [ALERTA] EL HOTEL FUE RESERVADO PERO LA APROBACIÓN MANUAL FUE RECHAZADA 🚨")
            handler_respuesta = RespuestaSagaHandler(orquestador)
            
            # Paso 1: Pagamos bien
            handler_respuesta.handle(PagoExitosoEvt(id_reserva=id_reserva, token_pasarela="token_ab123"))
            
            # Paso 2: El Hotel Aprobó
            print("\n--- 5. SIMULANDO RESPUESTA DEL PMS (HOTEL) [EXITOSA] ---")
            handler_respuesta.handle(ConfirmacionPmsExitosaEvt(id_reserva=id_reserva, codigo_pms="HTL-999"))
            
            # Paso 3: El Backoffice Rechazó
            print("\n--- 6. SIMULANDO APROBACION MANUAL [RECHAZADA] ---")
            from Booking.modulos.saga_reservas.dominio.eventos import ReservaRechazadaManualEvt
            handler_respuesta.handle(ReservaRechazadaManualEvt(id_reserva=id_reserva, motivo="El cliente está reportado"))
            
            print("\n🛑 SIMULACIÓN DE COMPENSACIÓN COMPLETADA 🛑\n")

        # VALIDACIÓN FINAL DE ESTADO EN BD
        from Booking.modulos.reserva.infraestructura.repositorios import RepositorioReservas
        repo = RepositorioReservas()
        
        # OBTENEMOS COMO STRING YA QUE SQLALCHEMY ESPERA STR EN LUGAR DE UUID DIRECTO EN ALGUNOS DIALECTOS
        reserva_final = repo.obtener_por_id(str(id_reserva))
        
        if reserva_final:
            print(f"📊 [ESTADO FINAL BD] Reserva {id_reserva} quedó en estado: {reserva_final.estado.name}")
        else:
            print(f"📊 [ESTADO FINAL BD] No se encontró la reserva en BD. (Verificar la sesión)")
            
        print("\n📜 [SAGA EXECUTION LOG] Bitácora en Base de Datos de la Transacción Distribuida:")
        saga_bd = repo_sagas.buscar_por_reserva(str(id_reserva))
        if saga_bd:
            for log in saga_bd.historial:
                hora = getattr(log, 'fecha_creacion', None)
                hora_str = hora.strftime('%H:%M:%S') if hora else "--:--:--"
                print(f"  [{hora_str}] {log.tipo_mensaje.name} -> {log.accion} | Payload: {log.payload_snapshot}")
        else:
            print("  [No se encontró instancia de saga]")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ["exito", "fallido"]:
        print("Uso: python3 simular_saga.py [exito|fallido]")
        sys.exit(1)

    app_global = create_app()
    
    modo = sys.argv[1]
    es_exito = modo == "exito"
    
    print(f"Ejecutando Camino {'Exitoso' if es_exito else 'de Fallo'}...")
    # Siempre limpiamos la BD en cada ejecución según lo solicitado
    run_simulation(app_global, init_db=True, happy_path=es_exito)
    
    print("\n\n" + "="*80)
    print("📊 [REPORTE GLOBAL DE LA BASE DE DATOS] Sagas Almacenadas")
    print("="*80)
    with app_global.app_context():
        from Booking.modulos.saga_reservas.infraestructura.dto import SagaInstanceDTO
        todas_sagas = db.session.query(SagaInstanceDTO).all()
        for s in todas_sagas:
            print(f" -> Saga {s.id_reserva[:8]}... | Estado Global: {s.estado_global}")
    print("\n")
