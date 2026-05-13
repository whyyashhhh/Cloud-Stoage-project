import logging
from cloud_backend.tasks.celery_app import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(name="cloud_backend.tasks.file_tasks.process_uploaded_file")
def process_uploaded_file(file_id: int, user_id: int) -> dict:
    logger.info(
        "post_upload_processing_started",
        extra={"file_id": file_id, "user_id": user_id},
    )

    # Simulated pipeline for interview/system-design flow.
    virus_scan_result = "clean"
    compressed = False
    thumbnail_generated = False

    logger.info(
        "post_upload_processing_completed",
        extra={
            "file_id": file_id,
            "user_id": user_id,
            "virus_scan": virus_scan_result,
            "compressed": compressed,
            "thumbnail_generated": thumbnail_generated,
        },
    )

    return {
        "file_id": file_id,
        "user_id": user_id,
        "virus_scan": virus_scan_result,
        "compressed": compressed,
        "thumbnail_generated": thumbnail_generated,
    }
