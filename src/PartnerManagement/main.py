from config.app import create_app
import uvicorn
from modules.partner.infrastructure.consumers.solicitar_aprobacion_consumer import start_consumer
# Inicializa la aplicación FastAPI (y levanta hilos de background de RabbitMQ)
app = create_app()

# Punto de entrada de la aplicación cuando es llamado por el motor de Python
if __name__ == "__main__":
    start_consumer()
    # Levanta el servidor usando Uvicorn en el puerto 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

