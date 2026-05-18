from redis import Redis

from cloud_backend.core.config import get_settings


settings = get_settings()
redis_client: Redis | None

try:
	redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
	redis_client.ping()
except Exception:
	redis_client = None
