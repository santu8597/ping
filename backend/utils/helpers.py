import os
from django.utils.crypto import get_random_string
from django.core.cache import caches
from django.contrib.auth.hashers import make_password, check_password
from django.core.files.storage import default_storage
# Helper function to generate OTP
from backend.utils.minio_handler import upload_file_to_minio
from config_env import CONFIG
from services.mailing import Mailing
from services_aiori_v2 import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import boto3


def generate_otp():
    return get_random_string(length=6, allowed_chars='1234567890')


def set_cache(cache_alias, key, value, timeout=300):
    """
    Set a value in the specified cache.

    Args:
    - cache_alias (str): The cache alias (e.g., 'otp_cache' or 'session_cache').
    - key (str): The cache key to store the value.
    - value (str): The value to store in the cache.
    - timeout (int): Cache expiration time in seconds (default is 5 minutes).

    Returns:
    - bool: True if the cache was set successfully, False otherwise.
    """
    try:
        cache = caches[cache_alias]
        cache.set(key, value, timeout)
        return True
    except Exception as e:
        # Log the error if needed
        return False


def get_cache(cache_alias, key):
    """
    Retrieve a value from the specified cache.

    Args:
    - cache_alias (str): The cache alias (e.g., 'otp_cache' or 'session_cache').
    - key (str): The cache key to retrieve.

    Returns:
    - str: The value stored in the cache or None if not found.
    """
    try:
        cache = caches[cache_alias]
        return cache.get(key)
    except Exception as e:
        # Log the error if needed
        return None


def delete_cache(cache_alias, key):
    """
    Delete a value from the specified cache.

    Args:
    - cache_alias (str): The cache alias (e.g., 'otp_cache' or 'session_cache').
    - key (str): The cache key to delete.

    Returns:
    - bool: True if the cache was deleted successfully, False otherwise.
    """
    try:
        cache = caches[cache_alias]
        cache.delete(key)
        return True
    except Exception as e:
        # Log the error if needed
        return False


def send_otp(email):
    try:
        if not email:
            return {"status": "error", "message": "Email is required."}

        # Generate and hash OTP
        otp = generate_otp()
        hashed_otp = make_password(otp)

        # Store OTP in Redis cache for 5 minutes
        if not set_cache('otp_cache', email, hashed_otp):
            return {"status": "error", "message": "Failed to store OTP in cache."}

        # Prepare email content
        content = {"otp": otp}

        # Send email
        email_helper = Mailing(
            email_type='otp',
            from_email=f"{CONFIG.DEFAULT_FROM_EMAIL}<{CONFIG.DEFAULT_FROM_EMAIL}>",
            email_address=email,
            content=content
        )
        email_response = email_helper.send_email()

        if email_response["status"] == "success":
            return {"status": "success", "message": "OTP sent successfully."}
        else:
            return {"status": "error", "message": email_response["message"]}

    except Exception as e:
        return {"status": "error", "message": f"An error occurred: {str(e)}"}


def handle_uploaded_file(file=None, user_id=None, base_folder="profile_image", public=False):
    """
    Saves uploaded file to MinIO and returns the object key for storing in DB.

    Args:
        file (UploadedFile): File to be saved.
        user_id (int or str, optional): User ID to include in path.
        base_folder (str): Base folder in MinIO bucket.
        public (bool): (Optional) Uploaded file type.

    Returns:
        str or None: Object key to store in DB, or None on failure.
    """
    if not file:
        return None

    result = upload_file_to_minio(file, user_id=user_id, base_folder=base_folder, public=public)

    if result["success"]:
        print("Uploaded to MinIO:", result["object_key"])
        print("Presigned URL (private):", result["url"])
        return result["url"]  # Store this in DB
    else:
        print("Upload failed:", result["error"])
        return None
