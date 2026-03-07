from config.app import create_app
from modules.pms.infrastructure.database import Base, engine
from modules.pms.infrastructure import models
from modules.pms.infrastructure.services.consumer import start_consumer

import threading

app = create_app()

Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def start_rabbitmq_consumer():

    thread = threading.Thread(target=start_consumer)
    thread.daemon = True
    thread.start()