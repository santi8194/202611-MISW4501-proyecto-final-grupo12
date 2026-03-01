# Microservicio de Booking - Experimento Saga

Este microservicio es el punto central del experimento para implementar y validar la consistencia transaccional mediante el patrón Saga Orquestada con recuperación LIFO (Last-In First-Out).

## Requisitos

- Python 3.12+
- Virtualenv o Conda

## Instalación y Configuración

1.  **Navegar a la carpeta y crear el entorno virtual**:
    ```bash
    cd src/Booking
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

## Ejecución del Servicio

Para levantar el servicio de Flask (Booking API):

```bash
export FLASK_APP=api
flask run --host=0.0.0.0 --port=5000
```

El servicio cuenta con los siguientes endpoints principales:
- `GET /health`: Estado de salud del servicio.
- `POST /api/reserva`: Crear una reserva en estado `HOLD`.
- `POST /api/reserva/<id>/formalizar`: Iniciar la SAGA de reserva.

## Simulación de la Saga (LIFO Engine)

Se ha creado un script especializado para validar el comportamiento del orquestador y la lógica de compensación sin necesidad de levantar infraestructura externa (RabbitMQ real). El script ahora soporta ejecución por parámetros para aislar los escenarios.

Para ejecutar la simulación (asegúrate de estar en la carpeta `src/Booking` y con el `venv` activo):

```bash
# Para ejecutar el Camino Feliz (Éxito completo)
python3 simular_saga.py exito

# Para ejecutar el Camino de Compensación (Fallo y Rollback LIFO)
python3 simular_saga.py fallido
```

### ¿Qué valida la simulación?
1.  **Camino Feliz (`exito`)**: Ejecución completa de la saga desde la creación de la reserva en HOLD, formalización, pago exitoso, confirmación en PMS, aprobación manual y envío de voucher. Al finalizar, la base de datos muestra el estado `COMPLETADA`.
2.  **Camino de Compensación (`fallido`)**: Simulación de un fallo en la aprobación manual (paso 3). El orquestador detecta el error y activa el motor LIFO para revertir en orden inverso: Cancela en PMS, reversa el pago y cancela la reserva local. Al finalizar, la base de datos muestra el estado `COMPENSACION_EXITOSA`.

**Nota:** Cada ejecución del script limpia la base de datos en memoria para asegurar que los resultados sean atómicos y fáciles de auditar en el reporte final.

## Flujo de la Saga

El experimento implementa una **Saga Orquestada** con el siguiente flujo de eventos y comandos:

### 1. Camino Feliz (Éxito)

1.  **Inicio**: Se recibe `CrearReservaHold` -> Estado `HOLD`.
2.  **Formalización**: Se recibe `FormalizarReserva` -> Estado `PENDIENTE` -> Emisión de `ReservaPendiente`.
3.  **Orquestación**: El Orquestador captura `ReservaPendiente`:
    *   Registra inicio de saga.
    *   Emite comando `ProcesarPagoCmd` a RabbitMQ.
4.  **Pago**: Se recibe `PagoExitosoEvt`:
    *   El Orquestador avanza el paso.
    *   Emite comando `ConfirmarReservaPmsCmd` (Hotel).
5.  **Confirmación**: Se recibe `ConfirmacionPmsExitosaEvt`:
    *   La saga marca el estado como `COMPLETADA`.

### 2. Camino de Compensación (Fallo LIFO)

Si ocurre un error (simulado mediante `RechazarReservaCmd`), el motor activa la recuperación en reversa:
1.  **Detección**: Se identifica el fallo.
2.  **Reversión LIFO**: El orquestador lee el `SagaExecutionLog` de la instancia de atrás hacia adelante:
    *   Si se emitió `ConfirmarReservaPmsCmd` -> Emite `CancelarReservaPmsCmd`.
    *   Si se emitió `ProcesarPagoCmd` -> Emite `ReversarPagoCmd`.
    *   **Final**: Emite `CancelarReservaLocalCmd` para liberar la reserva en Booking.
3.  **Cierre**: El estado de la saga queda en `COMPENSACION_EXITOSA`.

### Matriz de Pasos y Compensaciones (Routing Slip)

| Paso | Microservicio | Comando / Acción | Evento de Éxito | Recuperación (LIFO) |
| :--- | :--- | :--- | :--- | :--- |
| 0 | Booking (Local) | `CrearReservaLocalCmd`* | `ReservaCreadaIntegracionEvt` | `CancelarReservaLocalCmd` |
| 1 | Pagos | `ProcesarPagoCmd` | `PagoExitosoEvt` | `ReversarPagoCmd` |
| 2 | Hotel (PMS) | `ConfirmarReservaPmsCmd` | `ConfirmacionPmsExitosaEvt` | `CancelarReservaPmsCmd` |
| 3 | Backoffice | `SolicitarAprobacionManualCmd` | `ReservaAprobadaManualEvt` | - |
| 4 | Booking (Local) | `ConfirmarReservaLocalCmd` | `ReservaConfirmadaLocalEvt` | `CancelarReservaLocalCmd` |
| 5 | Notificador | `MarcarSagaEsperandoVoucher` | `VoucherEnviadoEvt` | `NotificarFalloTecnicoCmd` |

*\*El Paso 0 es inyectado virtualmente por el Orquestador al inicio para asegurar que la reserva inicial en HOLD sea cancelada si falla cualquier paso posterior.*

---
*Este proyecto es parte del experimento para el Proyecto Integrador I - Grupo 12*
