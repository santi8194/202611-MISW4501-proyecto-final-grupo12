# Microservicio de Booking - Experimento Saga

Este microservicio es el núcleo del experimento para validar la **consistencia transaccional distribuida** mediante el patrón **Saga Orquestada** con recuperación **LIFO** (Last-In First-Out).

## 🚀 Instalación y Configuración

### Requisitos
- Python 3.12+
- Docker y Docker Compose

### Configuración del Entorno Virtual (Local)
Si deseas ejecutar o depurar el código fuera de Docker:
```bash
cd src/Booking
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🛠️ Ejecución del Servicio

### Opción 1: Docker (Recomendada para E2E)
Desde la raíz `TravelHub`:
```bash
docker compose build booking-api booking-saga-worker
docker compose up -d
```
- **API**: [http://localhost:5001](http://localhost:5001)
- **RabbitMQ Management**: [http://localhost:15672](http://localhost:15672) (guest/guest)

### Opción 2: Desarrollo Local (Hot-Reload)
Para depuración rápida sin reconstruir imágenes:
1. Asegura que RabbitMQ/Redis de Docker estén arriba.
2. API (Terminal 1):
   ```bash
   export PYTHONPATH=$(pwd)/src
   export RABBITMQ_HOST=localhost
   uvicorn Booking.asgi:app --reload --port 5001
   ```
3. Saga Worker (Terminal 2):
   ```bash
   export PYTHONPATH=$(pwd)/src
   export RABBITMQ_HOST=localhost
   python src/Booking/modulos/saga_reservas/infraestructura/consumidor_evt_saga.py
   ```

---

## 📡 Infraestructura de Mensajería (RabbitMQ)

El sistema utiliza un diseño basado en **Exchanges de Tópico** para permitir enrutamiento dinámico.

- **Exchange de Eventos**: `travelhub.events.exchange` (Topic)
- **Exchange de Comandos**: `travelhub.commands.exchange` (Topic)

### Mapeo de Enrutamiento (Routing Keys)
| Tipo | Nombre | Routing Key |
| :--- | :--- | :--- |
| **Evento** | Reserva Creada | `evt.reserva.creada` |
| **Comando**| Procesar Pago | `cmd.payment.procesar-pago` |
| **Comando**| Confirmar Hotel | `cmd.pms.confirmar-reserva` |
| **Evento** | Pago Exitoso | `evt.pago.exitoso` |

---

## 🔄 Flujo de la Saga Orquestada

El orquestador utiliza un **Routing Slip** persistido en base de datos (`booking.db`) para determinar el siguiente paso.

### Matriz de Pasos y Recuperación
| Paso | Acción | Comando | Evento Esperado | Compensación (LIFO) |
| :--- | :--- | :--- | :--- | :--- |
| **0** | Inicio | `CrearReservaLocalCmd`* | `ReservaCreadaIntegracionEvt` | `CancelarReservaLocalCmd` |
| **1** | Cobro | `ProcesarPagoCmd` | `PagoExitosoEvt` | `ReversarPagoCmd` |
| **2** | Inventario | `ConfirmarReservaPmsCmd` | `ConfirmacionPmsExitosaEvt` | `CancelarReservaPmsCmd` |
| **3** | Revisión | `SolicitarAprobacionManualCmd`| `ReservaAprobadaManualEvt` | - |

*\*El Paso 0 es inyectado virtualmente para asegurar consistencia si falla el pago.*

---

## 🔍 Depuración y Monitoreo

### Verificación de Mensajes en Cola
Puedes inspeccionar si los comandos están llegando al broker:
```bash
docker exec -it proyecto-final-grupo12-rabbitmq-broker-1 rabbitmqadmin list queues
```

### Visualización de Logs
```bash
# Ver logs del API
docker logs -f proyecto-final-grupo12-booking-api-1

# Ver logs del Orquestador (Worker)
docker logs -f proyecto-final-grupo12-booking-saga-worker-1
```

### Simulación Agnóstica
Para probar la lógica del motor sin RabbitMQ:
```bash
python3 simular_saga.py exito
python3 simular_saga.py fallido
```

---
*Proyecto Integrador I - Grupo 12*
