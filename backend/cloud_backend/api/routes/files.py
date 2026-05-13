import logging
import uuid
from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from cloud_backend.api.deps import get_current_user
from cloud_backend.db.session import get_db
from cloud_backend.models.user import User
from cloud_backend.schemas.file import (
    CompleteMultipartRequest,
    DownloadUrlResponse,
    FileInitUploadRequest,
    FileInitUploadResponse,
    FileResponse,
    PresignedPartRequest,
    PresignedPartResponse,
    VersionResponse,
)
from cloud_backend.services.file_service import (
    complete_multipart_upload,
    delete_file,
    get_download_url,
    get_part_upload_url,
    init_multipart_upload,
    list_user_files,
    list_versions,
    restore_version,
)
from cloud_backend.tasks.file_tasks import process_uploaded_file
from cloud_backend.core.config import get_settings


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["files"])
settings = get_settings()


@router.put("/mock-upload-part")
async def mock_upload_part(
    key: str = Query(...),
    uploadId: str = Query(...),
    partNumber: int = Query(...),
):
    if partNumber < 1:
        return Response(status_code=400)
    etag = f'"{uuid.uuid4().hex}"'
    return Response(status_code=200, headers={"ETag": etag})


@router.get("/mock-download")
def mock_download(key: str = Query(...)):
    body = f"Mock S3 object content for key: {key}\n"
    return PlainTextResponse(content=body, media_type="application/octet-stream")


@router.post("/multipart/init", response_model=FileInitUploadResponse)
def init_upload(
    payload: FileInitUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_obj, session = init_multipart_upload(
        db=db,
        user_id=current_user.id,
        file_name=payload.file_name,
        file_size=payload.file_size,
        file_type=payload.file_type,
    )
    logger.info("multipart_init", extra={"file_id": file_obj.id, "user_id": current_user.id})
    return FileInitUploadResponse(
        file_id=file_obj.id,
        upload_id=session.upload_id,
        s3_key=session.s3_key,
        part_size=session.chunk_size_bytes,
        total_parts=session.total_parts,
    )


@router.post("/multipart/presign-part", response_model=PresignedPartResponse)
def presign_part(
    payload: PresignedPartRequest,
    current_user: User = Depends(get_current_user),
):
    url = get_part_upload_url(
        user_id=current_user.id,
        upload_id=payload.upload_id,
        s3_key=payload.s3_key,
        part_number=payload.part_number,
    )
    return PresignedPartResponse(
        part_number=payload.part_number,
        url=url,
        expires_in=settings.s3_presigned_expiry_seconds,
    )


@router.post("/multipart/complete")
def complete_upload(
    payload: CompleteMultipartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parts = [{"ETag": p.etag, "PartNumber": p.part_number} for p in payload.parts]
    file_obj = complete_multipart_upload(
        db=db,
        user_id=current_user.id,
        upload_id=payload.upload_id,
        s3_key=payload.s3_key,
        parts=parts,
    )
    process_uploaded_file.delay(file_obj.id, current_user.id)
    logger.info("multipart_complete", extra={"file_id": file_obj.id, "user_id": current_user.id})
    return {"message": "Upload completed", "file_id": file_obj.id}


@router.get("", response_model=list[FileResponse])
def get_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = list_user_files(db, current_user.id)
    response: list[FileResponse] = []
    for file_obj, version in rows:
        response.append(
            FileResponse(
                file_id=file_obj.id,
                user_id=file_obj.owner_id,
                file_name=file_obj.file_name,
                file_type=file_obj.file_type,
                status=file_obj.status,
                latest_version=file_obj.latest_version,
                upload_time=(version.upload_time if version else file_obj.created_at),
                file_size=(version.file_size if version else 0),
                s3_url=(version.s3_url if version else ""),
            )
        )
    return response


@router.get("/{file_id}/download-url", response_model=DownloadUrlResponse)
def get_download_presigned_url(
    file_id: int,
    version: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    url = get_download_url(db, current_user.id, file_id, version)
    logger.info("download_url_generated", extra={"file_id": file_id, "user_id": current_user.id})
    return DownloadUrlResponse(url=url, expires_in=settings.s3_presigned_expiry_seconds)


@router.get("/{file_id}/versions", response_model=list[VersionResponse])
def get_versions(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    versions = list_versions(db, current_user.id, file_id)
    return [
        VersionResponse(
            version_number=v.version_number,
            file_size=v.file_size,
            s3_url=v.s3_url,
            upload_time=v.upload_time,
        )
        for v in versions
    ]


@router.post("/{file_id}/versions/{version_number}/restore")
def restore(
    file_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_obj = restore_version(db, current_user.id, file_id, version_number)
    logger.info(
        "version_restored",
        extra={"file_id": file_id, "version": version_number, "user_id": current_user.id},
    )
    return {"message": "Version restored", "file_id": file_obj.id, "latest_version": file_obj.latest_version}


@router.delete("/{file_id}")
def remove_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_file(db, current_user.id, file_id)
    logger.info("file_deleted", extra={"file_id": file_id, "user_id": current_user.id})
    return {"message": "File deleted"}
