import os

from config.app import create_app
import uvicorn
from modules.partner.infrastructure.consumers.solicitar_aprobacion_consumer import start_consumer
# Inicializa la aplicación FastAPI (y levanta hilos de background de RabbitMQ)
app = create_app()

# Punto de entrada de la aplicación cuando es llamado por el motor de Python
if __name__ == "__main__":
    if os.getenv("ENABLE_RABBIT", "false") == "true":
        start_consumer()


