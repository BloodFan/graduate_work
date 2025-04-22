from redis.asyncio import Redis

from auth_app.src.core.config import redis_data

redis: Redis | None = None


async def get_redis() -> Redis:
    return Redis(unix_socket_path=redis_data.unix_socket_path, db=1)
