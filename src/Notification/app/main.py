from fastapi import FastAPI
from app.redis_client import get_redis_connection
from app.rabbitmq_client import publish_message

app = FastAPI(title="Notification Service")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/notifications")
async def send_notification(payload: dict):

    # Guardar en Redis
    redis_client = get_redis_connection()
    redis_client.set("last_notification", str(payload))

    # Enviar a RabbitMQ
    publish_message("notifications", str(payload))

    return {
        "message": "Notification sent",
        "data": payload
    }