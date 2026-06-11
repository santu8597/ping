from datetime import datetime, timedelta
from backend.users.serializers import *

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import os
from django.utils.crypto import get_random_string
from django.conf import settings

from rest_framework import generics, permissions, status, views, mixins
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import base64

class ProfileDeatailView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        user_id = user.id
        response_data = {}
        profile_image_name = ''

        rs = User.objects.filter(id=user_id, is_active=True, is_blocked=False, is_deleted=False)
        if rs:
            user_serialize = ProfileViewSerializer(rs, many=True)
            for details in user_serialize.data:
                profile_image_name = details['profile_image']
                if profile_image_name:
                    # Check if the file exists in MinIO
                    if default_storage.exists(profile_image_name):
                        with default_storage.open(profile_image_name, 'rb') as f:
                            base64_image = encode_image_base64(f)
                        details['profile_image'] = base64_image
            response_data['status'] = 1
            response_data['msg'] = 'Successfully get user details'
            response_data['profile_details'] = user_serialize.data
            http_status_code = 200
        else:
            response_data['status'] = 0
            response_data['msg'] = 'No data found'
            response_data['profile_details'] = []
            http_status_code = 404
        return Response(response_data, status=http_status_code)

    # def get(self, request, format=None):
    #     user = request.user
    #     user_id = user.id
    #     response_data = {}
    #     profile_image_name = ''
    #     rs = User.objects.filter(id=user_id, is_active=True, is_blocked=False, is_deleted=False)
    #     if rs:
    #         user_serialize = ProfileViewSerializer(rs, many=True)
    #         for details in user_serialize.data:
    #             profile_image_name = details['profile_image']
    #             if profile_image_name is not None:
    #                 if os.path.exists('media/profile_image/' + profile_image_name):
    #                     base64_image = encode_image_base64(settings.MEDIA_ROOT + '/profile_image/' + profile_image_name)
    #                     details['profile_image'] = base64_image
    #         response_data['status'] = 1
    #         response_data['msg'] = 'Successfully get user details'
    #         response_data['profile_details'] = user_serialize.data
    #         http_status_code = 200
    #     else:
    #         response_data['status'] = 0
    #         response_data['msg'] = 'No data found'
    #         response_data['profile_details'] = []
    #         http_status_code = 404
    #     return Response(response_data, status=http_status_code)
    

    def put(self, request, format=None):
        response_data = {}
        user = request.user
        user_id = user.id
        requestdata = request.data
        ## Check user is exist or not
        rs = User.objects.filter(id=user_id, is_active=True, is_blocked=False, is_deleted=False).first()
        if rs:
            obj = User.objects.filter(id=user_id).update(
                first_name=requestdata['first_name'],
                last_name=requestdata['last_name'],
                phone_no=requestdata['phone_no'],
                address=requestdata['address'],
                pin_code=requestdata['pin_code'],
                modified_date=timezone.now()
            )
            print('Success')
            response_data['status'] = 1
            response_data['message'] = "User updated successfuly"
            response_data['user_id'] = user_id
            return Response(response_data, status=200)
        else:
            print('Failure')
            response_data['status'] = 0
            response_data['message'] = "User not found"
            response_data['user_id'] = user_id
            return Response(response_data, status=200)

    def patch(self, request, format=None):
        response_data = {}
        user = request.user
        user_id = user.id
        request_data = request.data

        user_instance = User.objects.filter(
            id=user_id, is_active=True, is_blocked=False, is_deleted=False
        ).first()

        if not user_instance:
            return Response({
                'status': 0,
                'message': "User not found",
                'user_id': user_id
            }, status=404)

        # List of allowed fields to update
        allowed_fields = ['first_name', 'last_name', 'phone_no', 'address', 'pin_code', 'designation',
                          'company_name', 'institution_name', 'country', 'state', 'city',
                          'hndb_url', 'github_url', 'linkedin_url']
        updated_fields = {}

        for field in allowed_fields:
            if field in request_data:
                updated_fields[field] = request_data[field]

        if not updated_fields:
            return Response({
                'status': 0,
                'message': "No valid fields to update.",
                'user_id': user_id
            }, status=400)

        updated_fields['modified_date'] = timezone.now()

        User.objects.filter(id=user_id).update(**updated_fields)

        return Response({
            'status': 1,
            'message': "User partially updated successfully",
            'user_id': user_id
        }, status=200)


class FileUploadView(mixins.CreateModelMixin, generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    # def post(self, request, *args, **kwargs):
    #     user = request.user
    #     user_id = user.id
    #     file1 = request.FILES['file']  ## Uploaded file
    #     file_type = request.data['file_type']  ## file Type i.e. image / doc / pdf   etc
    #     up_dir = request.data['up_dir']
    #     result_list = {}
    #     new_file_name = ''
    #     full_path_name = ''
    #     upload_status = False
    #     base64_image = ''

    #     if file_type is None:
    #         file_type = "img"

    #     if up_dir is None:
    #         up_dir = "images"

    #     image_name = file1.name
    #     name1 = get_random_string(length=8)
    #     ext = image_name.split('.')[-1]
    #     now = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    #     # new_file_name 	= file_type+name1
    #     uploaded_file_name = now + '.' + ext

    #     #####################################
    #     ## Check File Type (Only 'jpg', 'jpeg', 'gif', 'png' allowe)
    #     if ext in ['jpg', 'jpeg', 'gif', 'png', 'pdf']:
    #         if not os.path.exists('media/' + str(up_dir) + '/'):
    #             os.makedirs('media/' + str(up_dir) + '/')
    #         upload_to = 'media/' + str(up_dir) + '/%s' % (uploaded_file_name)
    #         fullpath = settings.BASE_DIR + '/media/' + str(up_dir)
    #         destination = open(upload_to, 'wb+')
    #         for chunk in file1.chunks():
    #             destination.write(chunk)
    #         destination.close()
    #         obj = User.objects.filter(id=user_id).update(
    #             profile_image=uploaded_file_name
    #         )
    #         if os.path.exists('media/' + str(up_dir) + '/'):
    #             base64_image = encode_image_base64(settings.MEDIA_ROOT + '/profile_image/' + uploaded_file_name)

    #         data = {
    #             'status': 1,
    #             'base64_image': base64_image,
    #             'uploaded_file_name': uploaded_file_name,
    #             'uploaded_file_url': fullpath,
    #             'message': 'Uploaded Successfully',
    #         }
    #     else:
    #         data = {
    #             'status': 0,
    #             'base64_image': base64_image,
    #             'uploaded_file_name': '',
    #             'uploaded_file_url': '',
    #             'message': 'File extension error',
    #         }

    #     return Response(data)
    def post(self, request, *args, **kwargs):
        user = request.user
        user_id = user.id
        file1 = request.FILES['file']  # Uploaded file
        file_type = request.data.get('file_type', 'img')  # Default to "img"
        up_dir = request.data.get('up_dir', 'images')     # Default to "images"
        
        image_name = file1.name
        ext = image_name.split('.')[-1].lower()
        base64_image = ''
        uploaded_file_name = datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.' + ext
        full_path_key = f'{up_dir}/{uploaded_file_name}'

        if ext in ['jpg', 'jpeg', 'gif', 'png', 'pdf']:
            # Save file to MinIO
            default_storage.save(full_path_key, file1)

            # Optional: update user field (e.g., profile_image)
            User.objects.filter(id=user_id).update(profile_image=uploaded_file_name)

            # Base64 encode if it's an image
            if ext in ['jpg', 'jpeg', 'gif', 'png']:
                if default_storage.exists(full_path_key):
                    with default_storage.open(full_path_key, 'rb') as f:
                        base64_image = encode_image_base64(f)

            data = {
                'status': 1,
                'base64_image': base64_image,
                'uploaded_file_name': uploaded_file_name,
                'uploaded_file_url': default_storage.url(full_path_key),
                'message': 'Uploaded Successfully',
            }
        else:
            data = {
                'status': 0,
                'base64_image': '',
                'uploaded_file_name': '',
                'uploaded_file_url': '',
                'message': 'File extension error',
            }

        return Response(data)


# def encode_image_base64(full_path):
#     image = ''
#     if full_path != "":
#         with open(full_path, 'rb') as imgFile:
#             image = base64.b64encode(imgFile.read())
#     return image
def encode_image_base64(file_obj):
    """
    Accepts a file-like object, reads it, and returns base64-encoded string.
    """
    if not file_obj:
        return ''
    
    # Read binary data
    image_data = file_obj.read()

    # Encode to base64
    encoded = base64.b64encode(image_data).decode('utf-8')  # convert to str
    return encoded

class UserReportProfileView(APIView):
    def post(self,request):
        requestData = request.data
        user = request.user
        user_email = user.email
        response_data = {}
        admin_status = User.objects.filter(email=user_email, is_active=True, is_blocked=False, is_deleted=False).first()
        if admin_status.is_superuser:
            get_profile_details=User.objects.filter(id=requestData['user_id'], is_active=True, is_blocked=False, is_deleted=False)
            if get_profile_details:
                user_serialize = UserReportProfileViewSerializer(get_profile_details, many=True)
                response_data['status'] =1
                response_data['msg'] = "User Profile details"
                response_data['User_profile_details']= user_serialize.data
                http_status_code = 200
            else:
                response_data['status'] = 0
                response_data['msg']='No Deatils'
                response_data['User_profile_details'] = []
                http_status_code = 404
        else:
            response_data['status'] = 0
            response_data['msg']='you are not admin'
            response_data['User_profile_details'] = []
            http_status_code = 404
        return Response(response_data, status=http_status_code)