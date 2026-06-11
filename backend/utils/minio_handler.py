import logging
from backend.utils.minio_uploader import MinioUploader

logger = logging.getLogger(__name__)


def upload_file_to_minio(file, user_id=None, base_folder="uploads", public=False):
    """
    Uploads a file to MinIO using the uploader wrapper.

    Args:
        file (UploadedFile): The uploaded file object.
        user_id (int, optional): User ID for path.
        base_folder (str): Folder inside bucket.
        public (bool): If True, file will be public.

    Returns:
        dict: {
            "success": True/False,
            "object_key": str,
            "url": str,
            "error": str (if any)
        }
    """
    try:
        uploader = MinioUploader()
        object_key = uploader.upload_file(file, user_id, base_folder, public)

        if object_key:
            url = uploader.get_file_url(object_key) if public else uploader.generate_presigned_url(object_key)
            return {
                "success": True,
                "object_key": object_key,
                "url": url,
                "error": None
            }
        else:
            return {
                "success": False,
                "object_key": None,
                "url": None,
                "error": "Upload failed."
            }

    except Exception as e:
        logger.exception("MinIO upload failed.")
        return {
            "success": False,
            "object_key": None,
            "url": None,
            "error": str(e)
        }


def delete_file_from_minio(object_key):
    """
    Deletes a file from MinIO.

    Returns:
        bool: True if deleted, False otherwise
    """
    try:
        uploader = MinioUploader()
        return uploader.delete_file(object_key)
    except Exception as e:
        logger.exception(f"MinIO delete failed for {object_key}")
        return False


def get_file_url_from_minio(object_key, presigned=False, expiry=3600):
    """
    Gets URL of a file in MinIO.

    Args:
        object_key (str): S3 key (e.g. profile/123/avatar.png)
        presigned (bool): Generate signed URL if private
        expiry (int): Time in seconds for presigned URL

    Returns:
        str or None
    """
    try:
        uploader = MinioUploader()
        if presigned:
            return uploader.generate_presigned_url(object_key, expiry)
        return uploader.get_file_url(object_key)
    except Exception as e:
        logger.exception(f"MinIO get URL failed for {object_key}")
        return None


def file_exists_in_minio(object_key):
    """
    Checks whether a file exists in MinIO.

    Returns:
        bool
    """
    try:
        uploader = MinioUploader()
        return uploader.file_exists(object_key)
    except Exception as e:
        logger.exception(f"MinIO existence check failed for {object_key}")
        return False

def read_file_from_minio(object_key):
    """
    Reads a file from MinIO and returns its bytes.

    Args:
        object_key (str): The object key/path inside the bucket.

    Returns:
        bytes or None: File content, or None on failure.
    """
    try:
        uploader = MinioUploader()
        response = uploader.client.get_object(Bucket=uploader.bucket, Key=object_key)
        return response['Body'].read()
    except Exception as e:
        logger.exception(f"MinIO read failed for {object_key}")
        return None