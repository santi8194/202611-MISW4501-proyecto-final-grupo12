import threading

from config.app import create_app
from modules.payments.infrastructure.database import Base, engine
from modules.payments.infrastructure import models
from modules.payments.infrastructure.services.consumer import start_consumer    

app = create_app()
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def start_rabbitmq_consumer():

    thread = threading.Thread(target=start_consumer)
    thread.daemon = True
    thread.start()