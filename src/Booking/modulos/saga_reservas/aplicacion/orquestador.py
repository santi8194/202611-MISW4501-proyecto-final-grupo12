from Booking.modulos.saga_reservas.dominio.entidades import SagaInstance
from Booking.modulos.saga_reservas.dominio.objetos_valor import EstadoSaga, TipoMensajeSaga
from Booking.modulos.saga_reservas.infraestructura.repositorios import RepositorioSagas
from Booking.config.uow import UnidadTrabajoHibrida
from Booking.modulos.saga_reservas.dominio.eventos import (
    ProcesarPagoCmd, ConfirmarReservaPmsCmd, 
    CancelarReservaPmsCmd, ReversarPagoCmd, CancelarReservaLocalCmd
)
import uuid

class OrquestadorSagaReservas:
    def __init__(self, repositorio: RepositorioSagas, uow: UnidadTrabajoHibrida):
        self.repositorio = repositorio
        self.uow = uow

    # MAPA DE COMPENSACIONES (Lógica LIFO Core)
    # Si emití el Comando X, y falla el proceso, debo emitir el Comando Y para compensar.
    MAPA_COMPENSACION = {
        "ProcesarPagoCmd": ReversarPagoCmd,
        "ConfirmarReservaPmsCmd": CancelarReservaPmsCmd
    }

    def iniciar_saga(self, id_reserva: uuid.UUID, id_usuario: uuid.UUID, monto: float):
        """Invocado cuando la reserva inicial pasa a PENDIENTE"""
        with self.uow:
            saga = SagaInstance(
                id=uuid.uuid4(),
                id_reserva=id_reserva
            )
            # PASO 1: Emitimos comando hacia el microservicio de Pagos
            cmd_pago = ProcesarPagoCmd(id_reserva=id_reserva, monto=monto)
            saga.registrar_comando_emitido("ProcesarPagoCmd", {"monto": monto})
            
            # Persistir estado y enviar mensaje
            self.uow.agregar_eventos([cmd_pago])
            self.repositorio.agregar(saga)
            self.uow.commit()
            print(f"[Orquestador] Saga iniciada. Comando ProcesarPagoCmd emitido para reserva {id_reserva}")

    def manejar_pago_exitoso(self, id_reserva: uuid.UUID, id_habitacion: uuid.UUID):
        """Invocado cuando RabbitMQ nos dice que el pago pasó (PagoExitosoEvt)"""
        with self.uow:
            saga = self.repositorio.buscar_por_reserva(str(id_reserva))
            if not saga or saga.estado_global != EstadoSaga.EN_PROCESO:
                return
            
            # Avanzamos y registramos el evento que nos empujó
            saga.avanzar_paso(1, "PagoExitosoEvt", {"token": "dummy_token"})
            
            # PASO 2: Emitir evento hacia el PMS (Propety Management System)
            cmd_pms = ConfirmarReservaPmsCmd(id_reserva=id_reserva, id_habitacion=id_habitacion)
            saga.registrar_comando_emitido("ConfirmarReservaPmsCmd", {"habitacion": str(id_habitacion)})
            
            saga.estado_global = EstadoSaga.PAUSADA_ESPERANDO_HOTEL
            
            self.uow.agregar_eventos([cmd_pms])
            self.repositorio.actualizar(saga)
            self.uow.commit()
            print(f"[Orquestador] Pago Exitoso. Comando ConfirmarReservaPmsCmd emitido para reserva {id_reserva}")

    def manejar_confirmacion_pms(self, id_reserva: uuid.UUID):
        """Invocado por ConfirmacionPmsExitosaEvt"""
        with self.uow:
            saga = self.repositorio.buscar_por_reserva(str(id_reserva))
            if not saga or saga.estado_global != EstadoSaga.PAUSADA_ESPERANDO_HOTEL:
                return
            
            saga.avanzar_paso(2, "ConfirmacionPmsExitosaEvt", {"status": "ok"})
            saga.estado_global = EstadoSaga.COMPLETADA
            
            self.repositorio.actualizar(saga)
            # Al commitear, la saga queda FINALIZADA con éxito
            self.uow.commit()
            print(f"[Orquestador] Saga COMPLETADA EXITOSAMENTE para reserva {id_reserva}")

    def compensar_saga(self, id_reserva: uuid.UUID, motivo_fallo: str):
        """El motor LIFO que revierte la transacción distribuida"""
        with self.uow:
            saga = self.repositorio.buscar_por_reserva(str(id_reserva))
            if not saga or saga.estado_global in [EstadoSaga.COMPLETADA, EstadoSaga.COMPENSACION_EXITOSA]:
                return

            print(f"\n[ORQUESTADOR-FALLO] Iniciando compensación para reserva {id_reserva}. Motivo: {motivo_fallo}")
            saga.iniciar_compensacion(motivo_fallo)
            comandos_compensatorios = []

            # -------------------------------------------------------------
            # MAGIA LIFO (Last-In First-Out)
            # -------------------------------------------------------------
            # Leemos el historial de la saga al reves (reversed)
            historial_inverso = list(reversed(saga.historial))
            
            for log in historial_inverso:
                if log.tipo_mensaje == TipoMensajeSaga.COMANDO_EMITIDO:
                    comando_original = log.accion
                    
                    # Buscamos en el diccionario si este comando tiene un inverso
                    ClaseCompensacion = self.MAPA_COMPENSACION.get(comando_original)
                    
                    if ClaseCompensacion:
                        print(f" -> LIFO Reversando: {comando_original} ... generando {ClaseCompensacion.__name__}")
                        
                        # Instanciamos el comando inverso. 
                        # OJO: En la vida real, sacaríamos los parámetros exactos (monto, habitacion) del log.payload_snapshot
                        if ClaseCompensacion == ReversarPagoCmd:
                            cmd = ReversarPagoCmd(id_reserva=id_reserva, monto=log.payload_snapshot.get('monto', 0.0))
                            comandos_compensatorios.append(cmd)
                        elif ClaseCompensacion == CancelarReservaPmsCmd:
                            habitacion = log.payload_snapshot.get('habitacion', str(uuid.uuid4())) # fallback dummy
                            cmd = CancelarReservaPmsCmd(id_reserva=id_reserva, id_habitacion=uuid.UUID(habitacion))
                            comandos_compensatorios.append(cmd)

            # Finalmente, siempre debemos cancelar la reserva local inicial que se quedó en PENDIENTE
            print(" -> LIFO Final: Cancelando Reserva Local en Base de Datos de Booking")
            comandos_compensatorios.append(CancelarReservaLocalCmd(id_reserva=id_reserva))
            
            saga.estado_global = EstadoSaga.COMPENSACION_EXITOSA
            
            # Empujamos todos los comandos generados a la cola de la UoW
            self.uow.agregar_eventos(comandos_compensatorios)
            self.repositorio.actualizar(saga)
            self.uow.commit() # Dispara en cascada los mensajes reverse a RabbitMQ
            print(f"[ORQUESTADOR-FALLO] Compensación FINALIZADA OK para la reserva {id_reserva}\n")
