import os

class Settings:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_USER = "guest"
    RABBITMQ_PASS = "guest"

settings = Settings()