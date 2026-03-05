from asgiref.wsgi import WsgiToAsgi
from Booking.api import create_app

# Creamos la aplicación WSGI de Flask
flask_app = create_app()

# La envolvemos para que sea compatible con ASGI (Uvicorn)
app = WsgiToAsgi(flask_app)
