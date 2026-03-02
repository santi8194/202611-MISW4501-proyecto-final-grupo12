
from fastapi import FastAPI
from api.health import router as health_router

def create_app():
    app = FastAPI(title="Notification Service")
    app.include_router(health_router)
    return app
