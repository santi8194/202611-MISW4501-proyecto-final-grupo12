# ¿Cómo Probar la Saga de Booking?

Este documento explica cómo levantar y probar el flujo de la Saga Orquestada de Reservas. Dado que los microservicios externos (Payment, PMS, PartnerManagement, Notification) aún no están construidos, hemos diseñado un entorno de pruebas robusto que simula su comportamiento mediante RabbitMQ.

Existen dos formas de probar la Saga: una simulación rápida (en memoria/agnóstica) y una simulación completa (End-to-End con RabbitMQ).

---

## Opción 1: Simulación Agnóstica Rápida (Recomendada)
Esta opción ejecuta un script que interactúa directamente con el orquestador en memoria sin necesidad de levantar contenedores, workers, ni enviar mensajes a RabbitMQ. Es ideal para validar la lógica pura del orquestador y la persistencia en base de datos.

**Requisitos**: No requiere RabbitMQ. Solo Python.

```bash
# Entrar al directorio
cd src/Booking

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar Camino Feliz
python simular_saga.py exito

# Ejecutar Camino de Fallo (Compensación LIFO)
python simular_saga.py fallido
```

---

## Opción 2: Simulación Completa con RabbitMQ (End-to-End)
Esta opción levanta la infraestructura real. El `consumidor_evt_saga.py` (Worker) escuchará eventos desde RabbitMQ, mientras que un script especial (`simulador_microservicios.py`) actuará como si fuesen los microservicios externos, respondiendo a los comandos del Orquestador.

### 1. Levantar Infraestructura Base
Desde la raíz del proyecto (`TravelHub`), levanta únicamente la base de datos, Redis y RabbitMQ usando Docker Compose:
```bash
docker compose up -d rabbitmq-broker booking-db redis-db
```

### 2. Preparar el Entorno (En Terminales Separadas)
Abre 3 terminales. En cada una de ellas, ve a la carpeta `src/Booking`, activa el entorno virtual y define las variables de entorno:

```bash
cd src/Booking
source venv/bin/activate
export PYTHONPATH=$(pwd)/..
export RABBITMQ_HOST=localhost
```

### 3. Ejecutar los Componentes
Ejecuta un componente en cada una de las 3 terminales previamente preparadas:

**Terminal 1 (Worker de la Saga)**:
Este proceso es el cerebro de la saga, maneja el estado cruzándolo con la Base de Datos.
```bash
python modulos/saga_reservas/infraestructura/consumidor_evt_saga.py
```

**Terminal 2 (Simulador de Microservicios)**:
Este script simulará a `Payment`, `PMS`, `PartnerManagement` y `Notification`.
```bash
# Para simular Camino Feliz:
python simulador_microservicios.py --modo exito

# O para simular Camino con Fallos:
# python simulador_microservicios.py --modo fallo
```

**Terminal 3 (API del Booking)**:
Arranca la API para poder inyectar la reserva inicial. (Nota: Necesitas tener instalado `uvicorn` en tu entorno si usas asgi o levantar el script `__init__.py`).
```bash
# Opción Flask:
flask --app=api run --port=5001

# Opción Uvicorn (Recomendada):
uvicorn Booking.asgi:app --reload --port 5001
```

### 4. Disparar el Flujo
Una vez que el Worker, el Simulador y la API estén corriendo, dispara la creación de una reserva realizando la siguiente petición (por Postman, cURL o script):

```bash
# 1. Crear Reserva Hold
curl -X POST http://localhost:5001/api/reserva \
-H "Content-Type: application/json" \
-d '{"id_usuario": "123e4567-e89b-12d3-a456-426614174000", "id_habitacion": "987e6543-e21b-12d3-a456-426614174000", "monto": 1500.0}'

# 2. Formalizar Reserva (REEMPLAZA <ID_RESERVA> CON EL ID DEVUELTO EN EL PASO 1)
curl -X POST http://localhost:5001/api/reserva/<ID_RESERVA>/formalizar
```

**Validación**: Revisa las consolas de la `Terminal 1` y `Terminal 2`. Verás cómo los mensajes fluyen entre el orquestador y el simulador a través del broker, completando el ciclo hasta marcar la Saga como exitosa o compensada según el modo.


###Documentación 3
Dejar los contenedores corriendo para probar la saga.

```bash
docker compose down -v && docker compose up --build -d
docker compose logs -f booking-saga-worker booking-simulator

```