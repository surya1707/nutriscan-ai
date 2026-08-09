import json
import logging
from typing import Any, Optional
import redis.asyncio as redis
from .config import settings

logger = logging.getLogger(__name__)

# TTL is 24 hours in seconds
DEFAULT_TTL = 86400

class CacheClient:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.client = None

    async def get_client(self) -> redis.Redis:
        if self.client is None:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
        return self.client

    async def get_json(self, key: str) -> Optional[Any]:
        try:
            client = await self.get_client()
            data = await client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {e}")
        return None

    async def set_json(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        try:
            client = await self.get_client()
            await client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {e}")

cache = CacheClient()
