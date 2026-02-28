from Booking.modulos.saga_reservas.dominio.entidades import SagaInstance
from Booking.modulos.saga_reservas.dominio.objetos_valor import EstadoSaga, TipoMensajeSaga
from Booking.modulos.saga_reservas.infraestructura.repositorios import RepositorioSagas
from Booking.config.uow import UnidadTrabajoHibrida
from Booking.modulos.saga_reservas.dominio.eventos import (
    ProcesarPagoCmd, ConfirmarReservaPmsCmd, 
    CancelarReservaPmsCmd, ReversarPagoCmd, CancelarReservaLocalCmd
)
import uuid

# Mapeo a memoria de los comandos
DIR_COMANDOS = {
    "ProcesarPagoCmd": ProcesarPagoCmd,
    "ConfirmarReservaPmsCmd": ConfirmarReservaPmsCmd,
    "CancelarReservaPmsCmd": CancelarReservaPmsCmd,
    "ReversarPagoCmd": ReversarPagoCmd,
    "CancelarReservaLocalCmd": CancelarReservaLocalCmd
}

class OrquestadorSagaReservas:
    def __init__(self, repositorio: RepositorioSagas, uow: UnidadTrabajoHibrida):
        self.repositorio = repositorio
        self.uow = uow

    def _obtener_paso_actual(self, id_flujo: str, version: int, evento_disparador: str):
        pasos = self.repositorio.obtener_pasos_saga(id_flujo, version)
        for p in pasos:
            if p.paso_actual == evento_disparador:
                return p
        return None

    def _obtener_paso_por_comando_emitido(self, id_flujo: str, version: int, comando_emitido: str):
        pasos = self.repositorio.obtener_pasos_saga(id_flujo, version)
        for p in pasos:
            if p.comando_a_emitir == comando_emitido:
                return p
        return None

    def iniciar_saga(self, id_reserva: uuid.UUID, id_usuario: uuid.UUID, monto: float):
        """Invocado cuando la reserva inicial pasa a PENDIENTE"""
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
            
            # Buscar el paso correspondiente al inicio ("ReservaPendiente")
            paso = self._obtener_paso_actual(saga.id_flujo, saga.version_ejecucion, "ReservaPendiente")
            if not paso:
                print(f"[Orquestador] No se encontró paso para ReservaPendiente")
                return

            # Registramos el evento inicial (para que en reversa se compense primero o al final)
            saga.avanzar_paso(paso.orden, "ReservaPendiente", {"monto": monto})

            ComandoClase = DIR_COMANDOS.get(paso.comando_a_emitir)
            if ComandoClase:
                cmd = ComandoClase(id_reserva=id_reserva, monto=monto)
                saga.registrar_comando_emitido(paso.comando_a_emitir, {"monto": monto})
                self.uow.agregar_eventos([cmd])
                print(f"[Orquestador] Saga iniciada. Comando {paso.comando_a_emitir} emitido para reserva {id_reserva}")
            
            saga.paso_actual = paso.orden
            saga.estado_global = EstadoSaga.EN_PROCESO

            self.repositorio.agregar(saga)
            self.uow.commit()

    def manejar_pago_exitoso(self, id_reserva: uuid.UUID, id_habitacion: uuid.UUID):
        """Invocado cuando RabbitMQ nos dice que el pago pasó (PagoExitosoEvt)"""
        with self.uow:
            saga = self.repositorio.buscar_por_reserva(str(id_reserva))
            if not saga or saga.estado_global != EstadoSaga.EN_PROCESO:
                return
            
            paso = self._obtener_paso_actual(saga.id_flujo, saga.version_ejecucion, "PagoExitosoEvt")
            if not paso:
                return

            saga.avanzar_paso(paso.orden, "PagoExitosoEvt", {"habitacion": str(id_habitacion)})
            
            ComandoClase = DIR_COMANDOS.get(paso.comando_a_emitir)
            if ComandoClase:
                cmd = ComandoClase(id_reserva=id_reserva, id_habitacion=id_habitacion)
                saga.registrar_comando_emitido(paso.comando_a_emitir, {"habitacion": str(id_habitacion)})
                self.uow.agregar_eventos([cmd])
                print(f"[Orquestador] Pago Exitoso. Comando {paso.comando_a_emitir} emitido para reserva {id_reserva}")
            
            saga.estado_global = EstadoSaga.PAUSADA_ESPERANDO_HOTEL
            
            self.repositorio.actualizar(saga)
            self.uow.commit()

    def manejar_confirmacion_pms(self, id_reserva: uuid.UUID):
        """Invocado por ConfirmacionPmsExitosaEvt"""
        with self.uow:
            saga = self.repositorio.buscar_por_reserva(str(id_reserva))
            if not saga or saga.estado_global != EstadoSaga.PAUSADA_ESPERANDO_HOTEL:
                return
            
            paso = self._obtener_paso_actual(saga.id_flujo, saga.version_ejecucion, "ConfirmacionPmsExitosaEvt")
            if paso:
                saga.avanzar_paso(paso.orden, "ConfirmacionPmsExitosaEvt", {"status": "ok"})
                
                # Por simplicidad marcamos completado si el comando indicado es un marcador o no está en DIR_COMANDOS
                if paso.comando_a_emitir == "Pausar_EsperarRevisionHotel" or paso.comando_a_emitir == "MarcarSagaCompletada":
                    saga.estado_global = EstadoSaga.COMPLETADA
            else:
                saga.estado_global = EstadoSaga.COMPLETADA
            
            self.repositorio.actualizar(saga)
            self.uow.commit()
            print(f"[Orquestador] Saga COMPLETADA EXITOSAMENTE para reserva {id_reserva}")

    def compensar_saga(self, id_reserva: uuid.UUID, motivo_fallo: str):
        """El motor LIFO que revierte la transacción distribuida leyendo de los pasos parametrizados"""
        with self.uow:
            saga = self.repositorio.buscar_por_reserva(str(id_reserva))
            if not saga or saga.estado_global in [EstadoSaga.COMPLETADA, EstadoSaga.COMPENSACION_EXITOSA]:
                return

            print(f"\n[ORQUESTADOR-FALLO] Iniciando compensación para reserva {id_reserva}. Motivo: {motivo_fallo}")
            saga.iniciar_compensacion(motivo_fallo)
            comandos_compensatorios = []

            # -------------------------------------------------------------
            # LIFO BASADO EN LA TABLA DE DEFINICIÓN DE EVENTOS
            # -------------------------------------------------------------
            historial_inverso = list(reversed(saga.historial))
            
            for log in historial_inverso:
                if log.tipo_mensaje == TipoMensajeSaga.EVENTO_RECIBIDO:
                    evento_recibido = log.accion
                    
                    if evento_recibido == "RechazarReservaCmd":
                        continue

                    paso = self._obtener_paso_actual(saga.id_flujo, saga.version_ejecucion, evento_recibido)
                    if paso is None:
                        continue
                    if not paso.paso_compensacion:
                        continue

                    ClaseCompensacion = DIR_COMANDOS.get(paso.paso_compensacion)
                    if ClaseCompensacion:
                        print(f" -> LIFO Reversando: {evento_recibido} ... al emitir {ClaseCompensacion.__name__}")
                        
                        if ClaseCompensacion == ReversarPagoCmd:
                            cmd = ReversarPagoCmd(id_reserva=id_reserva, monto=1500.0)
                            comandos_compensatorios.append(cmd)
                        elif ClaseCompensacion == CancelarReservaPmsCmd:
                            habitacion = log.payload_snapshot.get('habitacion', str(uuid.uuid4()))
                            cmd = CancelarReservaPmsCmd(id_reserva=id_reserva, id_habitacion=uuid.UUID(habitacion))
                            comandos_compensatorios.append(cmd)
                        elif ClaseCompensacion == CancelarReservaLocalCmd:
                            cmd = CancelarReservaLocalCmd(id_reserva=id_reserva)
                            comandos_compensatorios.append(cmd)

            saga.estado_global = EstadoSaga.COMPENSACION_EXITOSA
            
            self.uow.agregar_eventos(comandos_compensatorios)
            self.repositorio.actualizar(saga)
            self.uow.commit()
            print(f"[ORQUESTADOR-FALLO] Compensación FINALIZADA OK para la reserva {id_reserva}\n")

