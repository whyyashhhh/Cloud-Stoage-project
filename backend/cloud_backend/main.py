from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from cloud_backend.api.routes.auth import router as auth_router
from cloud_backend.api.routes.files import router as files_router
from cloud_backend.core.config import get_settings
from cloud_backend.core.logging_config import configure_logging
from cloud_backend.db.base import Base
from cloud_backend.db.session import engine
from cloud_backend.services.rate_limiter import rate_limit


settings = get_settings()
configure_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-oriented cloud storage backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_prefix, dependencies=[Depends(rate_limit)])
app.include_router(files_router, prefix=settings.api_prefix, dependencies=[Depends(rate_limit)])


@app.get(f"{settings.api_prefix}/health")
def health() -> dict:
    return {"status": "healthy", "version": settings.app_version}


@app.get("/")
def root() -> dict:
    return {"message": settings.app_name, "version": settings.app_version}
