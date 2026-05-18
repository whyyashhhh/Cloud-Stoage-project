from fastapi import HTTPException, Request, status

from cloud_backend.core.config import get_settings
from cloud_backend.services.redis_service import redis_client


settings = get_settings()


async def rate_limit(request: Request) -> None:
    if redis_client is None:
        return

    ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{ip}"

    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, 60)

    if current > settings.rate_limit_requests_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
