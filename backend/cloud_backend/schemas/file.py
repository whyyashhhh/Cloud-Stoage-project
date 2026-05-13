from datetime import datetime
from pydantic import BaseModel


class FileInitUploadRequest(BaseModel):
    file_name: str
    file_size: int
    file_type: str = "application/octet-stream"


class FileInitUploadResponse(BaseModel):
    file_id: int
    upload_id: str
    s3_key: str
    part_size: int
    total_parts: int


class PresignedPartRequest(BaseModel):
    upload_id: str
    s3_key: str
    part_number: int


class PresignedPartResponse(BaseModel):
    part_number: int
    url: str
    expires_in: int


class CompletePart(BaseModel):
    etag: str
    part_number: int


class CompleteMultipartRequest(BaseModel):
    upload_id: str
    s3_key: str
    parts: list[CompletePart]


class FileResponse(BaseModel):
    file_id: int
    user_id: int
    file_name: str
    file_type: str
    status: str
    latest_version: int
    upload_time: datetime
    file_size: int
    s3_url: str


class DownloadUrlResponse(BaseModel):
    url: str
    expires_in: int


class VersionResponse(BaseModel):
    version_number: int
    file_size: int
    s3_url: str
    upload_time: datetime
