from Booking.modulos.saga_reservas.dominio.entidades import SagaInstance
from Booking.modulos.saga_reservas.dominio.objetos_valor import EstadoSaga, TipoMensajeSaga
from Booking.modulos.saga_reservas.infraestructura.repositorios import RepositorioSagas
from Booking.config.uow import UnidadTrabajoHibrida
from Booking.modulos.saga_reservas.dominio.eventos import (
    ProcesarPagoCmd, ConfirmarReservaPmsCmd, 
    CancelarReservaPmsCmd, ReversarPagoCmd, CancelarReservaLocalCmd,
    SolicitarAprobacionManualCmd, MarcarSagaEsperandoVoucherCmd
)
import uuid
import inspect

# Mapeo a memoria de los comandos
DIR_COMANDOS = {
    "ProcesarPagoCmd": ProcesarPagoCmd,
    "ConfirmarReservaPmsCmd": ConfirmarReservaPmsCmd,
    "CancelarReservaPmsCmd": CancelarReservaPmsCmd,
    "ReversarPagoCmd": ReversarPagoCmd,
    "CancelarReservaLocalCmd": CancelarReservaLocalCmd,
    "SolicitarAprobacionManualCmd": SolicitarAprobacionManualCmd,
    "MarcarSagaEsperandoVoucher": MarcarSagaEsperandoVoucherCmd
}

class OrquestadorSagaReservas:
    def __init__(self, repositorio: RepositorioSagas, uow: UnidadTrabajoHibrida):
        self.repositorio = repositorio
        self.uow = uow

    def _obtener_paso_actual(self, id_flujo: str, version: int, evento_disparador: str):
        pasos = self.repositorio.obtener_pasos_saga(id_flujo, version)
        for p in pasos:
            if p.evento == evento_disparador:
                return p
        return None

    def _obtener_paso_por_comando_emitido(self, id_flujo: str, version: int, comando_emitido: str):
        pasos = self.repositorio.obtener_pasos_saga(id_flujo, version)
        for p in pasos:
            if p.comando == comando_emitido:
                return p
        return None

    def _obtener_paso_por_error(self, id_flujo: str, version: int, error_evento: str):
        pasos = self.repositorio.obtener_pasos_saga(id_flujo, version)
        for p in pasos:
            if p.error == error_evento:
                return p
        return None

    def _procesar_siguiente_comando(self, saga: SagaInstance, pasos: list, siguiente_paso, id_reserva: uuid.UUID, kwargs_comando: dict = None, payload_registro: dict = None):
        if not siguiente_paso or not siguiente_paso.comando:
            return

        kwargs_comando = kwargs_comando or {}
        payload_registro = payload_registro or {}

        comando_nombre = siguiente_paso.comando
        saga.registrar_comando_emitido(comando_nombre, payload_registro)
        
        if comando_nombre == "ConfirmarReservaLocalCmd":
            print(f"[Orquestador] Interceptando Comando Local: {comando_nombre}. Procesando en memoria.")
            
            from Booking.modulos.reserva.infraestructura.repositorios import RepositorioReservas
            from Booking.config.db import db
            
            repo_reservas = RepositorioReservas()
            reserva = repo_reservas.obtener_por_id(str(id_reserva))
            
            if reserva:
                reserva.confirmar_reserva()
                repo_reservas.actualizar(reserva)
                db.session.commit()
                
                print(f"✅ [ORQUESTADOR -> LOCAL] Reserva {reserva.id} CONFIRMADA localmente en BD.")
                
                # Avanzamos al siguiente paso informando que ya lo hicimos
                saga.avanzar_paso(siguiente_paso.index, "ReservaConfirmadaLocalEvt", {})
                
                # Revisar si la saga completó el happy path local e instigarlo a continuar
                paso_final = next((p for p in pasos if p.index == siguiente_paso.index + 1), None)
                if paso_final:
                     saga.estado_global = EstadoSaga.EN_PROCESO
                     self._procesar_siguiente_comando(
                         saga=saga,
                         pasos=pasos,
                         siguiente_paso=paso_final,
                         id_reserva=id_reserva,
                         kwargs_comando={},
                         payload_registro={}
                     )
                else:
                    saga.estado_global = EstadoSaga.COMPLETADA
            else:
                print(f"❌ [ORQUESTADOR -> LOCAL] No se encontró la reserva {id_reserva} para confirmar.")
        else:
            ComandoClase = DIR_COMANDOS.get(comando_nombre)
            if ComandoClase:
                # Filtrar kwargs_comando usando inspect para instanciar el dataclass del comando
                # sin generar "got an unexpected keyword argument"
                sig = inspect.signature(ComandoClase.__init__)
                parametros_validos = sig.parameters.keys()
                
                kwargs_filtrados = {}
                for k, v in kwargs_comando.items():
                    if k in parametros_validos:
                        kwargs_filtrados[k] = v
                        
                # Hack temporal para la prueba de concepto y el routing slip:
                # Si el comando requiere datos que no fluyeron nativamente en el evento anterior (ej. Pago -> PMS)
                # los inyectamos como mock si están ausentes para no romper el DataClass strict init de Python:
                if 'id_habitacion' in parametros_validos and 'id_habitacion' not in kwargs_filtrados:
                    kwargs_filtrados['id_habitacion'] = uuid.uuid4()
                if 'monto' in parametros_validos and 'monto' not in kwargs_filtrados:
                    kwargs_filtrados['monto'] = 1500.0
                        
                if 'id_reserva' in kwargs_filtrados:
                    del kwargs_filtrados['id_reserva']
                    
                cmd = ComandoClase(id_reserva=id_reserva, **kwargs_filtrados)
                self.uow.agregar_eventos([cmd])
                print(f"[Orquestador] Comando Externo {comando_nombre} emitido para reserva {id_reserva}")
                self.uow.commit()

    def iniciar_saga(self, id_reserva: uuid.UUID, id_usuario: uuid.UUID, monto: float):
        """Invocado cuando la reserva inicial pasa a PENDIENTE"""
        try:
            with self.uow:
                definicion = self.repositorio.obtener_definicion_saga_activa("RESERVA_ESTANDAR")
                if not definicion:
                    print("[Orquestador] No se encontró definición de saga activa para RESERVA_ESTANDAR")
                    return

                saga = SagaInstance(
                    id=uuid.uuid4(),
                    id_reserva=id_reserva,
                    id_flujo=definicion.id_flujo,
                    version_ejecucion=definicion.version
                )
                
                # Buscamos el paso inicial (Index 0 del array, que corresponde a index=1 de la Saga).
                pasos = self.repositorio.obtener_pasos_saga(saga.id_flujo, saga.version_ejecucion)
                if not pasos or len(pasos) < 1:
                    print(f"[Orquestador] No hay pasos definidos")
                    return
                
                paso_inicial = pasos[0]

                # Registramos el evento inicial (para que en reversa se compense primero o al final)
                saga.avanzar_paso(paso_inicial.index, "ReservaCreadaIntegracionEvt", {"monto": monto})

                # Avanzamos al paso 1 inmediatamente
                siguiente_paso = pasos[1] if len(pasos) > 1 else None
                if siguiente_paso:
                    self._procesar_siguiente_comando(
                        saga=saga,
                        pasos=pasos,
                        siguiente_paso=siguiente_paso,
                        id_reserva=id_reserva,
                        kwargs_comando={"monto": monto},
                        payload_registro={"monto": monto}
                    )
                saga.estado_global = EstadoSaga.EN_PROCESO

                self.repositorio.agregar(saga)
                self.uow.commit()
                return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[Orquestador] Error crítico en iniciar_saga: {e}")
            return False

    def manejar_evento_respuesta(self, id_reserva: uuid.UUID, evento_recibido: str, payload_recibido: dict = None):
        """Manejador agnóstico de eventos. Escucha cualquier evento de compensación o avance y determina el próximo paso consultando la DB del Routing Slip."""
        payload_recibido = payload_recibido or {}
        
        with self.uow:
            saga = self.repositorio.buscar_por_reserva(str(id_reserva))
            if not saga or saga.estado_global not in [EstadoSaga.EN_PROCESO, EstadoSaga.PAUSADA_ESPERANDO_HOTEL]:
                return

            # Validar primero si el evento entrante es un error reportado (Fallo orgánico)
            paso_fallido = self._obtener_paso_por_error(saga.id_flujo, saga.version_ejecucion, evento_recibido)
            if paso_fallido:
                print(f"[Orquestador Agnostico] 🚨 Evento de error detectado: {evento_recibido}. Desviando a compensación.")
                self.compensar_saga(id_reserva, evento_recibido)
                return

            # Buscar en el routing slip (base de datos) qué paso produjo este evento como ÉXITO
            paso_actual = self._obtener_paso_actual(saga.id_flujo, saga.version_ejecucion, evento_recibido)
            if not paso_actual:
                print(f"[Orquestador Agnostico] Evento no reconocido o fuera de secuencia: {evento_recibido}")
                return

            # Marcamos que cerramos exitosamente el paso actual
            saga.avanzar_paso(paso_actual.index, evento_recibido, payload_recibido)

            # Buscar el siguiente paso configurado
            pasos = self.repositorio.obtener_pasos_saga(saga.id_flujo, saga.version_ejecucion)
            siguiente_paso = next((p for p in pasos if p.index == paso_actual.index + 1), None)

            if siguiente_paso:
                # Disparamos el comando siguiente
                self._procesar_siguiente_comando(
                    saga=saga, 
                    pasos=pasos, 
                    siguiente_paso=siguiente_paso, 
                    id_reserva=id_reserva, 
                    kwargs_comando=payload_recibido, # Re-inyectamos el payload anterior como inputs del nuevo comando
                    payload_registro=payload_recibido
                )
                
                # Regla de negocio temporal para pintar el estado de la saga
                if siguiente_paso.comando == "ConfirmarReservaPmsCmd":
                     saga.estado_global = EstadoSaga.PAUSADA_ESPERANDO_HOTEL
            else:
                # Si no hay siguiente paso, la saga terminó su happy path
                saga.estado_global = EstadoSaga.COMPLETADA
            
            self.repositorio.actualizar(saga)
            self.uow.commit()

    def compensar_saga(self, id_reserva: uuid.UUID, evento_fallo: str):
        """El motor LIFO que revierte la transacción distribuida leyendo de los pasos parametrizados"""
        with self.uow:
            saga = self.repositorio.buscar_por_reserva(str(id_reserva))
            if not saga or saga.estado_global in [EstadoSaga.COMPLETADA, EstadoSaga.COMPENSACION_EXITOSA]:
                return

            print(f"\n[ORQUESTADOR-FALLO] Iniciando compensación para reserva {id_reserva}. Evento fallo reportado: {evento_fallo}")
            saga.iniciar_compensacion(f"Fallo reportado: {evento_fallo}")
            comandos_compensatorios = []
            
            # Buscar si el evento_fallo coincide con un 'error' esperado en la definición
            paso_fallido = self._obtener_paso_por_error(saga.id_flujo, saga.version_ejecucion, evento_fallo)
            if paso_fallido:
                print(f"[Orquestador] El error '{evento_fallo}' corresponde al fallo del paso {paso_fallido.index} detonado por ({paso_fallido.evento})")

            # -------------------------------------------------------------
            # LIFO BASADO EN LA TABLA DE DEFINICIÓN DE EVENTOS
            # -------------------------------------------------------------
            historial_inverso = list(reversed(saga.historial))
            
            for log in historial_inverso:
                if log.tipo_mensaje == TipoMensajeSaga.EVENTO_RECIBIDO:
                    evento_recibido = log.accion
                    
                    if evento_recibido == evento_fallo:
                        continue

                    paso = self._obtener_paso_actual(saga.id_flujo, saga.version_ejecucion, evento_recibido)
                    if paso is None:
                        continue
                    if not paso.compensacion:
                        continue

                    ClaseCompensacion = DIR_COMANDOS.get(paso.compensacion)
                    if ClaseCompensacion:
                        print(f" -> LIFO Reversando: {evento_recibido} ... al emitir {ClaseCompensacion.__name__}")
                        
                        kwargs_log = {}
                        
                        if ClaseCompensacion == ReversarPagoCmd:
                            cmd = ReversarPagoCmd(id_reserva=id_reserva, monto=1500.0)
                            comandos_compensatorios.append(cmd)
                            kwargs_log = {"monto": 1500.0}
                        elif ClaseCompensacion == CancelarReservaPmsCmd:
                            habitacion = log.payload_snapshot.get('habitacion', str(uuid.uuid4()))
                            cmd = CancelarReservaPmsCmd(id_reserva=id_reserva, id_habitacion=uuid.UUID(habitacion))
                            comandos_compensatorios.append(cmd)
                            kwargs_log = {"id_habitacion": str(habitacion)}
                        elif ClaseCompensacion == CancelarReservaLocalCmd:
                            print(f"[Orquestador-Fallo] Interceptando Comando Local para Compensación: CancelarReservaLocalCmd")
                            from Booking.modulos.reserva.aplicacion.handlers import CancelarReservaLocalHandler
                            from Booking.modulos.reserva.infraestructura.repositorios import RepositorioReservas
                            
                            handler_local_fallo = CancelarReservaLocalHandler(
                                repositorio=RepositorioReservas(), 
                                uow=self.uow
                            )
                            # Ejecuta el borrado local sincrónicamente:
                            evento_falla = handler_local_fallo.handle(CancelarReservaLocalCmd(id_reserva=id_reserva))
                        
                        saga.registrar_comando_emitido(ClaseCompensacion.__name__, kwargs_log)

            saga.estado_global = EstadoSaga.COMPENSACION_EXITOSA
            
            self.uow.agregar_eventos(comandos_compensatorios)
            self.repositorio.actualizar(saga)
            self.uow.commit()
            print(f"[ORQUESTADOR-FALLO] Compensación FINALIZADA OK para la reserva {id_reserva}\n")

