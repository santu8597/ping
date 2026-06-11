import boto3
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.text import slugify


class MinioUploader:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME

    def generate_object_key(self, file_name, user_id=None, base_folder="uploads"):
        ext = file_name.split('.')[-1]
        base_name = slugify(file_name.rsplit('.', 1)[0])[:50]
        unique_name = f"{base_name}_{get_random_string(8)}.{ext}"

        key_parts = [base_folder]
        if user_id:
            key_parts.append(str(user_id))
        key_parts.append(unique_name)

        return "/".join(key_parts)

    def upload_file(self, file, user_id=None, base_folder="uploads", public=False):
        object_key = self.generate_object_key(file.name, user_id, base_folder)
        content_type = getattr(file, 'content_type', 'application/octet-stream')

        extra_args = {"ContentType": content_type}
        if public:
            extra_args["ACL"] = "public-read"

        try:
            self.client.upload_fileobj(file, self.bucket, object_key, ExtraArgs=extra_args)
            print(f"✅ File uploaded to: {object_key}")
            return object_key
        except Exception as e:
            print("❌ Upload failed:", str(e))
            return None

    def get_file_url(self, object_key):
        return f"{settings.AWS_S3_ENDPOINT_URL}/{self.bucket}/{object_key}"

    def delete_file(self, object_key):
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)
            print(f"🗑️ Deleted file: {object_key}")
            return True
        except Exception as e:
            print("❌ Delete failed:", str(e))
            return False

    def file_exists(self, object_key):
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except self.client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            print("⚠️ File existence check failed:", str(e))
            return False

    def generate_presigned_url(self, object_key, expiry=3600):
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expiry
            )
            return url
        except Exception as e:
            print("Presigned URL generation failed:", str(e))
            return None
