import os
import uuid
from pathlib import Path
from google.cloud import storage
from config import GCS_PROJECT_ID, GCS_BUCKET_NAME, GCS_CREDENTIALS_PATH


class GCSService:
    """Service for handling Google Cloud Storage operations.

    Falls back to local disk storage when Google Cloud Storage is not configured,
    so the app remains usable in development without ADC credentials.
    """

    def __init__(self):
        """Initialize storage mode."""
        if GCS_CREDENTIALS_PATH:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCS_CREDENTIALS_PATH

        self.client = None
        self.bucket = None
        self.use_local_storage = not (GCS_PROJECT_ID and GCS_BUCKET_NAME)
        self.local_storage_dir = Path(__file__).resolve().parent / "local_storage"
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_bucket(self):
        if self.use_local_storage:
            return None

        if self.bucket is None:
            self.client = storage.Client(project=GCS_PROJECT_ID)
            self.bucket = self.client.bucket(GCS_BUCKET_NAME)
        return self.bucket

    def _local_file_path(self, gcs_path: str) -> Path:
        return self.local_storage_dir / gcs_path

    def upload_file(self, file_content: bytes, original_filename: str, user_id: int) -> str:
        """Upload a file to cloud storage or local fallback storage."""
        file_extension = original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
        unique_filename = f"{user_id}/{uuid.uuid4().hex}"
        if file_extension:
            unique_filename += f".{file_extension}"

        if self.use_local_storage:
            file_path = self._local_file_path(unique_filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(file_content)
            return unique_filename

        bucket = self._ensure_bucket()
        blob = bucket.blob(unique_filename)
        blob.upload_from_string(file_content)
        return unique_filename

    def download_file(self, gcs_path: str) -> bytes:
        """Download a file from cloud storage or local fallback storage."""
        if self.use_local_storage:
            return self._local_file_path(gcs_path).read_bytes()

        bucket = self._ensure_bucket()
        blob = bucket.blob(gcs_path)
        return blob.download_as_bytes()

    def delete_file(self, gcs_path: str) -> bool:
        """Delete a file from cloud storage or local fallback storage."""
        if self.use_local_storage:
            file_path = self._local_file_path(gcs_path)
            if file_path.exists():
                file_path.unlink()
            return True

        bucket = self._ensure_bucket()
        blob = bucket.blob(gcs_path)
        blob.delete()
        return True

    def file_exists(self, gcs_path: str) -> bool:
        """Check if a file exists in cloud storage or local fallback storage."""
        if self.use_local_storage:
            return self._local_file_path(gcs_path).exists()

        bucket = self._ensure_bucket()
        blob = bucket.blob(gcs_path)
        return blob.exists()


# Initialize GCS service
gcs_service = GCSService()
