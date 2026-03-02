
from config.app import create_app
from modules.consumers.reserva_confirmada_consumer import start_consumer

app = create_app()

if __name__ == "__main__":
    start_consumer()
