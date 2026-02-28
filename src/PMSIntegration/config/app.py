from fastapi import FastAPI
from api.router import router

def create_app():
    app = FastAPI(title="PMS Integration Service")
    app.include_router(router)
    return app