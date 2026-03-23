from config.app import create_app
from modules.pms.infrastructure.database import Base, engine
from modules.pms.infrastructure import models
from modules.pms.infrastructure.services.consumer import start_consumer

import threading
import os

app = create_app()

Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def start_rabbitmq_consumer():
    if os.getenv("ENABLE_RABBIT", "false") == "true":
        thread = threading.Thread(target=start_consumer)
        thread.daemon = True
        thread.start()