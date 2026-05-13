# FAANG-Level Cloud Storage Backend Blueprint

## 1) Clean Backend Architecture

```text
Client (Web/Mobile/Postman)
        |
        v
FastAPI API Gateway (auth routes + file routes)
        |
        v
Auth Layer (JWT access + refresh, bcrypt)
        |
        v
File Service (multipart upload orchestration, access control, versioning)
        |
        +--------------------+
        |                    |
        v                    v
PostgreSQL (metadata)    AWS S3 (file objects)
        |
        v
Redis (rate limiting, cache, Celery broker/result)
        |
        v
Celery Workers (post-upload async processing)
```

Implemented modules:
- cloud_backend/main.py
- cloud_backend/api/routes/auth.py
- cloud_backend/api/routes/files.py
- cloud_backend/services/auth_service.py
- cloud_backend/services/file_service.py
- cloud_backend/services/s3_service.py
- cloud_backend/services/rate_limiter.py
- cloud_backend/tasks/file_tasks.py

## 2) API Endpoints List

Base prefix: /api/v1

Authentication:
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- POST /auth/logout
- GET /auth/me

Storage + Upload + Versioning:
- POST /files/multipart/init
- POST /files/multipart/presign-part
- POST /files/multipart/complete
- GET /files
- GET /files/{file_id}/download-url
- GET /files/{file_id}/versions
- POST /files/{file_id}/versions/{version_number}/restore
- DELETE /files/{file_id}

Health:
- GET /health
- GET /

## 3) PostgreSQL Schema (SQL)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(120) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'processing',
    latest_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE file_versions (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_size INTEGER NOT NULL,
    s3_key VARCHAR(512) UNIQUE NOT NULL,
    s3_url VARCHAR(1024) NOT NULL,
    upload_time TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(file_id, version_number)
);

CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    jti VARCHAR(64) UNIQUE NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE upload_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    upload_id VARCHAR(255) UNIQUE NOT NULL,
    s3_key VARCHAR(512) NOT NULL,
    total_parts INTEGER NOT NULL,
    chunk_size_bytes INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_files_status ON files(status);
CREATE INDEX idx_file_versions_file_id ON file_versions(file_id);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_upload_sessions_user_id ON upload_sessions(user_id);
```

## 4) Production-Level Folder Structure

```text
backend/
  app.py                      # compatibility entrypoint -> cloud_backend.main
  requirements.txt
  Dockerfile
  FAANG_UPGRADE_BLUEPRINT.md
  cloud_backend/
    main.py
    api/
      deps.py
      routes/
        auth.py
        files.py
    core/
      config.py
      security.py
      logging_config.py
    db/
      base.py
      session.py
    models/
      user.py
      file.py
      file_version.py
      refresh_token.py
      upload_session.py
    schemas/
      auth.py
      file.py
    services/
      auth_service.py
      file_service.py
      s3_service.py
      redis_service.py
      rate_limiter.py
    tasks/
      celery_app.py
      file_tasks.py
```

## 5) Step-by-Step Implementation Plan

Phase 1 - Foundation:
1. Add centralized config, DB session, model base.
2. Split monolith into route/service/model layers.
3. Add structured JSON logging.

Phase 2 - Auth hardening:
1. Add bcrypt password hashing.
2. Add JWT access + refresh token pair.
3. Persist refresh tokens with jti + hash and revoke support.

Phase 3 - S3 migration:
1. Replace local/GCS direct upload with S3 multipart.
2. Add pre-signed upload-part URLs.
3. Add pre-signed download URLs.

Phase 4 - Large file resilience:
1. Add upload session table.
2. Add part-based resume flow.
3. Finalize upload with ETag list and complete call.

Phase 5 - Security and abuse prevention:
1. Add strict ownership checks for every file action.
2. Add Redis IP rate limiting middleware.
3. Add token-type validation and expiration handling.

Phase 6 - Async processing:
1. Add Celery worker.
2. Trigger post-upload pipeline task.
3. Add processing lifecycle status in file metadata.

Phase 7 - Versioning:
1. Add file_versions table.
2. Keep latest_version pointer.
3. Add list/restore endpoints.

Phase 8 - Operability:
1. Add Docker Compose services (API, Postgres, Redis, Worker).
2. Add health checks.
3. Add logging fields for uploads/downloads/deletes.

## 6) Optional Deployment Strategy (Docker + Cloud)

Option A - AWS ECS Fargate:
1. Push backend image to ECR.
2. Run API and worker as separate ECS services.
3. Use RDS PostgreSQL + ElastiCache Redis + S3.
4. Put API behind ALB + WAF.
5. Use CloudWatch logs/metrics and alarms.

Option B - Kubernetes:
1. Deploy API and worker as separate Deployments.
2. Use HPA for API pods and worker autoscaling.
3. Attach IAM role via IRSA for S3 access.
4. Use managed Postgres/Redis.

Critical production add-ons:
- Alembic migrations for schema control.
- OpenTelemetry traces.
- Antivirus integration (e.g., ClamAV service).
- KMS encryption + bucket policies + VPC endpoints.
- CDN for download acceleration.
