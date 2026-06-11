from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sessions.models import Session
from django.utils.crypto import get_random_string
from django.conf import settings

from rest_framework import generics, permissions, status, views, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
import json
from django.http import JsonResponse
from django.http import HttpResponse

from datetime import datetime, timedelta
from backend.users.serializers import *
from backend.common.serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

import django.db.models
from django.db.models import Q
from backend.anchor.models import *
from backend.subscription.models import *
from backend.users.models import *
from django.core.mail import send_mail
import random
from django.utils import timezone
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class JSONResponse(HttpResponse):
    """ An HttpResponse that renders its content into JSON. """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        # kwargs['access_control_allow_origin'] = '*'
        super(JSONResponse, self).__init__(content, **kwargs)


def encode_image_base64(full_path):
    image = ''
    if full_path != "":
        with open(full_path, 'rb') as imgFile:
            image = base64.b64encode(imgFile.read())
    return image


class BlogFileUploadView(mixins.CreateModelMixin, generics.ListAPIView):
    # permission_classes = (IsAuthenticated,)

    # def post(self, request, *args, **kwargs):
    #     user = request.user
    #     user_id = user.id
    #     print('&&&&&&&&&&&&& Upload &&&&&&&&&&&&&&&&', request.data['UploadFiles'])
    #     file1 = request.FILES['UploadFiles']  ## Uploaded file
    #     # file_type 	= request.data['file_type']		## file Type i.e. image / doc / pdf   etc
    #     up_dir = None
    #     result_list = {}
    #     new_file_name = ''
    #     full_path_name = ''
    #     upload_status = False
    #     base64_image = ''

    #     # if file_type is  None:
    #     #     file_type =  "img"

    #     if up_dir is None:
    #         up_dir = "blog_images"

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
    #             base64_image = encode_image_base64(settings.MEDIA_ROOT + '/blog_images/' + uploaded_file_name)

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
        file1 = request.FILES['UploadFiles']  # Uploaded file

        up_dir = "blog_images"
        base64_image = ''
        image_name = file1.name
        ext = image_name.split('.')[-1].lower()
        uploaded_file_name = datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.' + ext
        full_path_key = f'{up_dir}/{uploaded_file_name}'

        if ext in ['jpg', 'jpeg', 'gif', 'png', 'pdf']:
            # Save to MinIO
            default_storage.save(full_path_key, file1)

            # OPTIONAL: update user's profile image (remove if not related to blog)
            User.objects.filter(id=user_id).update(profile_image=uploaded_file_name)

            # Base64 encode only if it's an image
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


class BlogFileDeletView(mixins.CreateModelMixin, generics.ListAPIView):
    # permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        user_id = user.id
        #print('&&&&&&&&&&&&& Upload &&&&&&&&&&&&&&&&', request.data)
        data = {
            'status': 1,
            'base64_image': base64_image,
            'uploaded_file_name': uploaded_file_name,
            'uploaded_file_url': fullpath,
            'message': 'Uploaded Successfully',
        }
        return Response(data)
