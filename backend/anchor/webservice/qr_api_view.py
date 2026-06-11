import re
from datetime import date, datetime

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.utils.minio_uploader import MinioUploader


class QrCodeListAPIView(APIView):
    CACHE_KEY = "qr_code_list_cache"
    CACHE_TTL = 300  

    def parse_filename_for_metadata(self, key):
        """Extracts userid and date from filename using regex."""
        match = re.search(r'userid[_-](\d+).*?(\d{4}-\d{2}-\d{2})', key)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def fetch_qr_files_from_minio(self):
        uploader = MinioUploader()
        prefix = "qr_code/"
        allowed_exts = (".png", ".jpg", ".jpeg")

        paginator = uploader.client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=uploader.bucket, Prefix=prefix)

        qr_files = []
        for page in pages:
            for obj in page.get('Contents', []):
                key = obj['Key']
                if not key.lower().endswith(allowed_exts):
                    continue

                userid, file_date = self.parse_filename_for_metadata(key)
                if not file_date:
                    file_date = obj['LastModified'].date().isoformat()

                try:
                    parsed_date = datetime.strptime(file_date, "%Y-%m-%d").date()
                except ValueError:
                    continue

                qr_files.append({
                    "name": key.split("/")[-1],
                    "url": uploader.get_file_url(key),
                    "date": parsed_date,
                    "userid": userid,
                })

        return qr_files

    def get(self, request):
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        today = date.today()
        if (start_date and not end_date) or (end_date and not start_date):
            return Response(
                {"error": "Both start_date and end_date must be provided together."},
                status=status.HTTP_400_BAD_REQUEST
            )


        # fetching data from cache
        cached_qr_files = cache.get(self.CACHE_KEY)
        if cached_qr_files is None:
            try:
                cached_qr_files = self.fetch_qr_files_from_minio()
                cache.set(self.CACHE_KEY, cached_qr_files, self.CACHE_TTL)
            except Exception as e:
                return Response(
                    {"error": f"Failed to fetch QR files: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        qr_files = cached_qr_files

        # error handling for date filtering
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                if start > end:
                    return Response({"error": "Start date must be before end date."}, status=status.HTTP_400_BAD_REQUEST)

                qr_files = [f for f in qr_files if start <= f["date"] <= end]
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Return latest 10 from today for pagenation
            qr_files = [f for f in qr_files if f["date"] == today]
            qr_files = sorted(qr_files, key=lambda x: x["name"], reverse=True)[:10]

        for file in qr_files:
            file["date"] = file["date"].isoformat()

        return Response({"qr_files": qr_files}, status=status.HTTP_200_OK)
