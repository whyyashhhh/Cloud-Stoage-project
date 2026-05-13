import os
from functools import lru_cache


class Settings:
    app_name: str = os.getenv("APP_NAME", "Cloud Storage FAANG Backend")
    app_version: str = os.getenv("APP_VERSION", "2.0.0")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://clouduser:cloudpassword@localhost:5432/cloud_storage",
    )

    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    rate_limit_requests_per_minute: int = int(os.getenv("RATE_LIMIT_RPM", "120"))

    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
    s3_endpoint_url: str | None = os.getenv("AWS_S3_ENDPOINT_URL")  # For LocalStack/Minio
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "cloud-storage-dev")
    s3_presigned_expiry_seconds: int = int(os.getenv("S3_PRESIGNED_EXPIRY_SECONDS", "900"))
    multipart_chunk_size_mb: int = int(os.getenv("MULTIPART_CHUNK_SIZE_MB", "8"))

    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", redis_url)
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", redis_url)

    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
