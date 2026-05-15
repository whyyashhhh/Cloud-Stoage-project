from typing import Any
import logging
import boto3
import uuid
from urllib.parse import quote
from botocore.exceptions import ClientError, NoCredentialsError

from cloud_backend.core.config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self) -> None:
        self.bucket = settings.s3_bucket_name
        self.use_mock = False
        self.mock_uploads: dict[str, dict[str, Any]] = {}  # For mocking multipart uploads

        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            logger.warning("No AWS credentials found; using mock S3 service")
            self.use_mock = True
            self.client = None
            return

        try:
            session = boto3.session.Session(
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
            # Use endpoint_url for LocalStack development or other S3-compatible services
            endpoint_url = getattr(settings, 's3_endpoint_url', None)
            self.client = session.client("s3", endpoint_url=endpoint_url)

            # Try to list buckets to verify credentials work
            try:
                self.client.list_buckets()
            except NoCredentialsError:
                logger.warning("No AWS credentials found; using mock S3 service for development")
                self.use_mock = True
                self.client = None
        except Exception as e:
            logger.warning("Failed to initialize S3 client; using mock S3 service: %s", e)
            self.use_mock = True
            self.client = None

    def start_multipart_upload(self, key: str, content_type: str) -> str:
        """Start a multipart upload"""
        if self.use_mock or self.client is None:
            # Generate a mock upload ID
            upload_id = str(uuid.uuid4())
            self.mock_uploads[upload_id] = {
                "key": key,
                "content_type": content_type,
                "parts": {},
            }
            print(f"📦 [Mock S3] Started multipart upload: {upload_id}")
            return upload_id
        
        try:
            response = self.client.create_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                ContentType=content_type,
            )
            return response["UploadId"]
        except NoCredentialsError:
            logger.warning("Falling back to mock S3 for multipart upload")
            self.use_mock = True
            return self.start_multipart_upload(key, content_type)

    def get_presigned_upload_part_url(self, key: str, upload_id: str, part_number: int) -> str:
        """Get a presigned URL for uploading a part"""
        if self.use_mock or self.client is None:
            encoded_key = quote(key, safe="")
            return (
                "http://localhost:8000/api/v1/files/mock-upload-part"
                f"?key={encoded_key}&uploadId={upload_id}&partNumber={part_number}"
            )
        
        try:
            return self.client.generate_presigned_url(
                "upload_part",
                Params={
                    "Bucket": self.bucket,
                    "Key": key,
                    "UploadId": upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=settings.s3_presigned_expiry_seconds,
            )
        except NoCredentialsError:
            logger.warning("Falling back to mock S3 for presigned URL")
            self.use_mock = True
            return self.get_presigned_upload_part_url(key, upload_id, part_number)

    def complete_multipart_upload(
        self, key: str, upload_id: str, parts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Complete a multipart upload"""
        if self.use_mock or self.client is None:
            # Mock completion
            if upload_id in self.mock_uploads:
                mock_data = self.mock_uploads[upload_id]
                del self.mock_uploads[upload_id]
            
            location = f"s3://{self.bucket}/{key}"
            logger.info("[Mock S3] Completed multipart upload: %s -> %s", upload_id, location)
            return {
                "Location": location,
                "Bucket": self.bucket,
                "Key": key,
                "ETag": f'"{uuid.uuid4().hex}"',
            }
        
        try:
            return self.client.complete_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
        except NoCredentialsError:
            print("⚠️  Falling back to mock S3 for complete multipart")
            self.use_mock = True
            return self.complete_multipart_upload(key, upload_id, parts)

    def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        """Abort a multipart upload"""
        if self.use_mock or self.client is None:
            if upload_id in self.mock_uploads:
                del self.mock_uploads[upload_id]
            logger.info("[Mock S3] Aborted multipart upload: %s", upload_id)
            return
        
        try:
            self.client.abort_multipart_upload(Bucket=self.bucket, Key=key, UploadId=upload_id)
        except NoCredentialsError:
            self.use_mock = True
            self.abort_multipart_upload(key, upload_id)

    def get_presigned_download_url(self, key: str) -> str:
        """Get a presigned URL for downloading an object"""
        if self.use_mock or self.client is None:
            encoded_key = quote(key, safe="")
            return f"http://localhost:8000/api/v1/files/mock-download?key={encoded_key}"
        
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=settings.s3_presigned_expiry_seconds,
            )
        except NoCredentialsError:
            self.use_mock = True
            return self.get_presigned_download_url(key)

    def delete_object(self, key: str) -> None:
        """Delete an object"""
        if self.use_mock or self.client is None:
            logger.info("[Mock S3] Deleted object: %s", key)
            return
        
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except NoCredentialsError:
            self.use_mock = True
            self.delete_object(key)


s3_service = S3Service()
