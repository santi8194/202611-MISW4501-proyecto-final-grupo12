import redis
from app.config import settings

def get_redis_connection():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=6379,
        decode_responses=True
    )