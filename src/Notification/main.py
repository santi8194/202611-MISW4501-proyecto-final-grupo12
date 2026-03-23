
import os
from config.app import create_app
from modules.consumers.reserva_confirmada_consumer import start_consumer

app = create_app()

if __name__ == "__main__":
    if os.getenv("ENABLE_RABBIT", "false") == "true":
        start_consumer()
