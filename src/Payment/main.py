from config.app import create_app
import uvicorn
from modules.payments.infrastructure.database import Base, engine
from modules.payments.infrastructure import models
from modules.payments.infrastructure.services.consumer import start_consumer    

app = create_app()
Base.metadata.create_all(bind=engine)
if __name__ == "__main__":
    start_consumer()
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)