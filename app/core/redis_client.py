from redis import asyncio as redis

from app.core.config import settings
from app.interfaces import RedisStorage


redis_client = redis.Redis(**settings.redis.REDIS_URL_ASYNC)
redis_storage = RedisStorage(redis_client)
