from datetime import datetime
import math
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from cloud_backend.core.config import get_settings
from cloud_backend.models.file import File
from cloud_backend.models.file_version import FileVersion
from cloud_backend.models.upload_session import UploadSession
from cloud_backend.services.s3_service import s3_service


settings = get_settings()


def _require_owned_file(db: Session, user_id: int, file_id: int) -> File:
    file_obj = db.query(File).filter(File.id == file_id, File.owner_id == user_id).first()
    if not file_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file_obj


def init_multipart_upload(
    db: Session,
    user_id: int,
    file_name: str,
    file_size: int,
    file_type: str,
) -> tuple[File, UploadSession]:
    existing_file = (
        db.query(File)
        .filter(File.owner_id == user_id, File.file_name == file_name)
        .first()
    )

    if existing_file:
        file_obj = existing_file
        next_version = existing_file.latest_version + 1
        existing_file.latest_version = next_version
        existing_file.status = "processing"
    else:
        # Generate unique S3 path for this file
        s3_path_key = f"s3/{uuid.uuid4().hex}/{file_name}"
        
        file_obj = File(
            owner_id=user_id,
            # Legacy columns for backward compatibility
            filename=file_name,
            original_filename=file_name,
            file_size=file_size,
            mime_type=file_type,
            gcs_path=s3_path_key,
            # New columns for S3 multipart
            file_name=file_name,
            file_type=file_type,
            status="processing",
            latest_version=1,
        )
        db.add(file_obj)
        db.flush()
        next_version = 1

    chunk_size = settings.multipart_chunk_size_mb * 1024 * 1024
    total_parts = max(1, math.ceil(file_size / chunk_size))

    key = f"users/{user_id}/files/{file_obj.id}/v{next_version}-{uuid.uuid4().hex}-{file_name}"
    upload_id = s3_service.start_multipart_upload(key=key, content_type=file_type)

    session = UploadSession(
        user_id=user_id,
        file_id=file_obj.id,
        upload_id=upload_id,
        s3_key=key,
        total_parts=total_parts,
        chunk_size_bytes=chunk_size,
    )
    db.add(session)
    db.commit()
    db.refresh(file_obj)
    db.refresh(session)
    return file_obj, session


def get_part_upload_url(user_id: int, upload_id: str, s3_key: str, part_number: int) -> str:
    if part_number < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid part number")
    return s3_service.get_presigned_upload_part_url(
        key=s3_key,
        upload_id=upload_id,
        part_number=part_number,
    )


def complete_multipart_upload(
    db: Session,
    user_id: int,
    upload_id: str,
    s3_key: str,
    parts: list[dict],
) -> File:
    session = (
        db.query(UploadSession)
        .filter(
            UploadSession.upload_id == upload_id,
            UploadSession.user_id == user_id,
            UploadSession.s3_key == s3_key,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")

    file_obj = _require_owned_file(db, user_id=user_id, file_id=session.file_id)

    s3_response = s3_service.complete_multipart_upload(
        key=s3_key,
        upload_id=upload_id,
        parts=parts,
    )

    version = FileVersion(
        file_id=file_obj.id,
        version_number=file_obj.latest_version,
        file_size=0,
        s3_key=s3_key,
        s3_url=s3_response.get("Location", ""),
        upload_time=datetime.utcnow(),
    )
    db.add(version)
    file_obj.status = "ready"
    db.delete(session)
    db.commit()
    db.refresh(file_obj)
    return file_obj


def get_download_url(db: Session, user_id: int, file_id: int, version: int | None = None) -> str:
    file_obj = _require_owned_file(db, user_id=user_id, file_id=file_id)
    target_version = version or file_obj.latest_version

    file_version = (
        db.query(FileVersion)
        .filter(FileVersion.file_id == file_id, FileVersion.version_number == target_version)
        .first()
    )
    if not file_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    return s3_service.get_presigned_download_url(file_version.s3_key)


def list_user_files(db: Session, user_id: int) -> list[tuple[File, FileVersion | None]]:
    files = db.query(File).filter(File.owner_id == user_id).all()
    result: list[tuple[File, FileVersion | None]] = []
    for file_obj in files:
        version = (
            db.query(FileVersion)
            .filter(
                FileVersion.file_id == file_obj.id,
                FileVersion.version_number == file_obj.latest_version,
            )
            .first()
        )
        result.append((file_obj, version))
    return result


def list_versions(db: Session, user_id: int, file_id: int) -> list[FileVersion]:
    _require_owned_file(db, user_id=user_id, file_id=file_id)
    return (
        db.query(FileVersion)
        .filter(FileVersion.file_id == file_id)
        .order_by(FileVersion.version_number.desc())
        .all()
    )


def restore_version(db: Session, user_id: int, file_id: int, version_number: int) -> File:
    file_obj = _require_owned_file(db, user_id=user_id, file_id=file_id)
    version = (
        db.query(FileVersion)
        .filter(FileVersion.file_id == file_id, FileVersion.version_number == version_number)
        .first()
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    file_obj.latest_version = version_number
    db.commit()
    db.refresh(file_obj)
    return file_obj


def delete_file(db: Session, user_id: int, file_id: int) -> None:
    file_obj = _require_owned_file(db, user_id=user_id, file_id=file_id)
    versions = db.query(FileVersion).filter(FileVersion.file_id == file_id).all()
    for ver in versions:
        s3_service.delete_object(ver.s3_key)

    db.delete(file_obj)
    db.commit()
