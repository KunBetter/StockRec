import json
from typing import Any, Optional

import redis.asyncio as aioredis
from loguru import logger

_redis: Optional[aioredis.Redis] = None


async def init_redis(redis_url: str) -> aioredis.Redis:
    global _redis
    if _redis is not None:
        return _redis

    try:
        _redis = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30,
        )
        await _redis.ping()
        logger.info(f"Redis connected: {redis_url}")
    except Exception as e:
        logger.warning(f"Redis unavailable ({e}), running without cache")
        _redis = None

    return _redis


async def get_redis() -> Optional[aioredis.Redis]:
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


async def cache_get(key: str) -> Optional[str]:
    if _redis is None:
        return None
    try:
        return await _redis.get(key)
    except Exception:
        return None


async def cache_set(key: str, value: str, ttl: int = 300) -> bool:
    if _redis is None:
        return False
    try:
        await _redis.setex(key, ttl, value)
        return True
    except Exception:
        return False


async def cache_delete(key: str) -> bool:
    if _redis is None:
        return False
    try:
        await _redis.delete(key)
        return True
    except Exception:
        return False


async def cache_get_json(key: str) -> Optional[Any]:
    raw = await cache_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def cache_set_json(key: str, value: Any, ttl: int = 300) -> bool:
    return await cache_set(key, json.dumps(value, ensure_ascii=False), ttl)
