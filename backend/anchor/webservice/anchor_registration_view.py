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
from datetime import datetime, timedelta, date
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import django.db.models
from django.db.models import Max, Count, Sum, Avg
from django.db.models import F,Q
from backend.anchor.models import *
from backend.users.models import *
from backend.anchor.serializers import *
from backend.users.serializers import *
import json
from django.utils import timezone
import requests
import os
import base64
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import PIL
from PIL import Image
from pyzbar.pyzbar import decode
import io
from backend.utils.minio_handler import read_file_from_minio, upload_file_to_minio
# import qrtools

# def read_qr_code(file_path):
#     # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', "QR CODE")
#     data = decode(Image.open(settings.MEDIA_ROOT + '/' + file_path))
#     decoded = ''
#     for d in data:
#         # print(d.data)
#         str_decoded = d.data.decode()
#         # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& STR DECODED &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', str_decoded)
#     return str_decoded


def read_qr_code(object_key):
    image_bytes = read_file_from_minio(object_key)

    if not image_bytes:
        print("No image bytes returned from MinIO.")
        return ""

    try:
        image = Image.open(io.BytesIO(image_bytes))

        gray_image = image.convert('L')  # Convert to grayscale
        decoded_data = decode(gray_image)

        if not decoded_data:
            print("QR code not detected in image.")
            return ''

        decoded = decoded_data[0].data.decode()
        print("QR Code Decoded:", decoded)
        return decoded

    except Exception as e:
        print("QR decode exception:", e)
        return ''

def encode_image_base64(full_path):
	image = ''
	if full_path != "":
		with open(full_path, 'rb') as imgFile:
			image = base64.b64encode(imgFile.read())
	return image
    
# def save_qrcode_in_file(imgstring):
#     uploaded_file_name = datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.png'
#     up_dir  	= 'qr_code'
#     imgdata = base64.b64decode(imgstring)
#     if not os.path.exists('media/' + str(up_dir) + '/'):
#         os.makedirs('media/' + str(up_dir) + '/')
#     upload_to = 'media/' + str(up_dir) + '/%s' % (uploaded_file_name)
#     # print('&&&&&&&&&&', uploaded_file_name)
#     fullpath = str(up_dir) + '/' + uploaded_file_name
#     with open(upload_to, 'wb') as f:
#         f.write(imgdata)
#     f.close()
#     # print(fullpath)
#     # print(settings.MEDIA_ROOT + '/' + str(up_dir) + '/' + uploaded_file_name)
#     return fullpath


def save_qrcode_in_file(imgstring, user_id=None):
    """
    Saves a base64-encoded QR image to MinIO.

    Args:
        imgstring (str): Base64-encoded PNG string.
        user_id (int, optional): Used for folder structuring.

    Returns:
        str or None: Object key (MinIO path) if successful, else None.
    """
    uploaded_file_name = datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.png'
    folder = 'qr_code'

    # Decode base64 image data and wrap it as a Django ContentFile
    imgdata = base64.b64decode(imgstring)
    file = ContentFile(imgdata)
    file.name = uploaded_file_name

    # Upload using the unified MinIO uploader
    result = upload_file_to_minio(file=file, user_id=user_id, base_folder=folder, public=True)

    if result['success']:
        return result['object_key']  # return MinIO object key
    return None

# def save_qrcode_file(data):
#     file1 		= data   		## Uploaded file
#     image_name 	= file1.name
#     name1 		= get_random_string(length=8)
#     ext 		= image_name.split('.')[-1]
#     now = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
#     uploaded_file_name 		= now+'.'+ext
#
#     # uploaded_file_name = datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.png'
#     up_dir  	= 'qr_code'
#     if not os.path.exists('media/' + str(up_dir) + '/'):
#         os.makedirs('media/' + str(up_dir) + '/')
#     upload_to = 'media/' + str(up_dir) + '/%s' % (uploaded_file_name)
#     # print('&&&&&&&&&&', uploaded_file_name)
#     fullpath = str(up_dir) + '/' + uploaded_file_name
#     destination = open(upload_to, 'wb+')
#     for chunk in file1.chunks():
#         destination.write(chunk)
#     destination.close()
#     # print(fullpath)
#     # print(settings.MEDIA_ROOT + '/' + str(up_dir) + '/' + uploaded_file_name)
#     return fullpath


def save_qrcode_file(data, user_id=None):
    """
    Saves a QR code file (UploadedFile) to MinIO and returns the object key.

    Args:
        data (UploadedFile): The uploaded image file.
        user_id (int, optional): For organizing uploads in user-specific folders.

    Returns:
        str or None: MinIO object key if successful, else None.
    """
    image_name = data.name
    ext = image_name.split('.')[-1]
    now = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    data.name = f'{now}.{ext}'

    folder = 'qr_code'

    result = upload_file_to_minio(file=data, user_id=user_id, base_folder=folder, public=True)

    if result['success']:
        return result['object_key']
    return None
def anchor_coordinate_summery_reset_operations(user_anchor_id):
    # print('hi')
    ##### Start: Create Delet Array Set For GroupWiseAncherLocationLabel #####
    rs_by_record = UserAnchor.objects.filter(id=user_anchor_id).first()
    deleted_country = rs_by_record.country
    deleted_state = rs_by_record.administrative_area_level_1
    deleted_city = rs_by_record.location

    rs_by_country = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=rs_by_record.country).values('country').annotate(anchor_count=Count('id'))
    
    ##### Start: Create Decrise Array Set For GroupWiseAncherLocationLabel #####
    i = 0
    set_array = []
    if rs_by_country:
        for c in rs_by_country:
            rs_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('id', flat=True)

            rs_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('latitude', flat=True)

            rs_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('longitude', flat=True)

            set_array.append(c)
            set_array[i]['parent_id'] = 1
            set_array[i]['user_anchor_ids'] = list(rs_user_anchor_ids)
            set_array[i]['user_anchor_latitude'] = list(rs_user_anchor_latitude)
            set_array[i]['user_anchor_longitude'] = list(rs_user_anchor_longitude)

            rs_by_state = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=rs_by_record.administrative_area_level_1).values('administrative_area_level_1').annotate(anchor_count=Count('id'))
            
            if rs_by_state:
                j = 0
                set_array[i]['states'] = list(rs_by_state)
                for s in rs_by_state:
                    rs_state_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values_list('id', flat=True)

                    rs_state_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values_list('latitude', flat=True)

                    rs_state_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values_list('longitude', flat=True)   

                    rs_by_city = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=rs_by_record.location).values('location').annotate(anchor_count=Count('id'))
                    set_array[i]['states'][j]['parent_id'] = 2
                    set_array[i]['states'][j]['user_anchor_ids'] = list(rs_state_user_anchor_ids)
                    set_array[i]['states'][j]['user_anchor_latitude'] = list(rs_state_user_anchor_latitude)
                    set_array[i]['states'][j]['user_anchor_longitude'] = list(rs_state_user_anchor_longitude)
                    
                    if rs_by_city:
                        k = 0
                        set_array[i]['states'][j]['cities'] = list(rs_by_city)
                        for ct in rs_by_city:
                            rs_city_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('id', flat=True)

                            rs_city_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('latitude', flat=True)

                            rs_city_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('longitude', flat=True)

                            set_array[i]['states'][j]['cities'][k]['parent_id'] = 2
                            set_array[i]['states'][j]['cities'][k]['user_anchor_ids'] = list(rs_city_user_anchor_ids)
                            set_array[i]['states'][j]['cities'][k]['user_anchor_latitude'] = list(rs_city_user_anchor_latitude)
                            set_array[i]['states'][j]['cities'][k]['user_anchor_longitude'] = list(rs_city_user_anchor_longitude)
                            k = k+1
                    else:
                        default_city_array = [{
                            "location": deleted_city,
                            "anchor_count": 0,
                            "parent_id": 2,
                            "user_anchor_ids": [],
                            "user_anchor_latitude": [],
                            "user_anchor_longitude": []
                        }]
                        set_array[i]['states'][j]['cities'] = default_city_array
                    j = j+1
            else:
                default_state_array = [{
                "administrative_area_level_1": deleted_state,
                "anchor_count": 0,
                "parent_id": 2,
                "user_anchor_ids": [],
                "user_anchor_latitude": [],
                "user_anchor_longitude": [],
                "cities": [{
                        "location": deleted_city,
                        "anchor_count": 0,
                        "parent_id": 2,
                        "user_anchor_ids": [],
                        "user_anchor_latitude": [],
                        "user_anchor_longitude": []
                    }]
            }]
                set_array[i]['states'] = default_state_array
            i = i+1
    else:
        #### Create Blank Obj Set #####
        set_array.append({
        "country": deleted_country,
        "anchor_count": 0,
        "parent_id": 1,
        "user_anchor_ids": [],
        "user_anchor_latitude": [],
        "user_anchor_longitude": [],
        "states": [{
                "administrative_area_level_1": deleted_state,
                "anchor_count": 0,
                "parent_id": 2,
                "user_anchor_ids": [],
                "user_anchor_latitude": [],
                "user_anchor_longitude": [],
                "cities": [{
                        "location": deleted_city,
                        "anchor_count": 0,
                        "parent_id": 2,
                        "user_anchor_ids": [],
                        "user_anchor_latitude": [],
                        "user_anchor_longitude": []
                    }]
            }]
    })
    #### Create Blank Obj Set #####

    ###### Update the Deleted Record ###########
    if len(set_array) > 0:
        for c in set_array:
            country_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, state__isnull=True, city__isnull=True, country=c['country']).update(user_anchor_ids= c['user_anchor_ids'], user_anchor_latitudes= c['user_anchor_latitude'], user_anchor_longitude= c['user_anchor_longitude'], regiser_anchor_count=c['anchor_count'])

            if len(c['states']) > 0:
                for s in c['states']:
                    state_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city__isnull=True, state=s['administrative_area_level_1'], country=c['country']).update(user_anchor_ids= s['user_anchor_ids'], user_anchor_latitudes= s['user_anchor_latitude'], user_anchor_longitude= s['user_anchor_longitude'], regiser_anchor_count=s['anchor_count'])

                    if len(s['cities']) > 0:
                        for ct in s['cities']:
                            city_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city=ct['location'], state=s['administrative_area_level_1'], country=c['country']).update(user_anchor_ids= ct['user_anchor_ids'], user_anchor_latitudes= ct['user_anchor_latitude'], user_anchor_longitude= ct['user_anchor_longitude'], regiser_anchor_count=ct['anchor_count'])

        ###### Update the Deleted Record ###########
    

class AnchorView(APIView):
    permission_classes = (IsAuthenticated,)
    # def get(self,request):
    #     user = request.user
    #     user_id = user.id
    #     response_data = {}
    #     rs=Anchor.objects.filter(is_deleted=False, is_blocked=False).order_by('anchor_name')
    #     if rs:
    #         serializer = AnchorSerializer(rs, many=True)
    #         for n in serializer.data:
    #             # print(n)
    #             user_anchor_rs = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, anchor_id=n['id']).first()
    #             if user_anchor_rs:
    #                 # print('Anchor is Register')
    #                 n['username'] = user_anchor_rs.user.username
    #                 n['location'] = user_anchor_rs.location
    #             else:
    #                 # print('Anchor Is not Register')
    #                 n['username'] = "NA"
    #                 n['location'] = "NA"
    #         response_data['status'] = 1
    #         response_data['message'] = 'Anchor list.'
    #         response_data['anchor'] = serializer.data
    #         return JsonResponse(response_data, status=200)
    #     else:
    #         response_data['status'] = 0
    #         response_data['message'] = 'Anchor list blank.'
    #         response_data['anchor'] = []
    #         return JsonResponse(response_data, status=200)
    def get(self, request):
        response_data = {}

        # Get anchors
        anchors = Anchor.objects.filter(is_deleted=False, is_blocked=False).order_by('anchor_name')
        if not anchors.exists():
            response_data['status'] = 0
            response_data['message'] = 'Anchor list blank.'
            response_data['anchor'] = []
            return JsonResponse(response_data, status=200)

        serializer = AnchorSerializer(anchors, many=True)

        # Fetch all UserAnchor records for these anchors in one go
        user_anchors = UserAnchor.objects.filter(
            is_blocked=False, is_deleted=False, anchor_id__in=[a.id for a in anchors]
        ).select_related("user")

        # Map anchor_id → (username, location)
        user_anchor_map = {ua.anchor_id: (ua.user.username, ua.location) for ua in user_anchors}

        # Attach username & location
        for anchor in serializer.data:
            if anchor['id'] in user_anchor_map:
                anchor['username'], anchor['location'] = user_anchor_map[anchor['id']]
            else:
                anchor['username'] = "NA"
                anchor['location'] = "NA"

        response_data['status'] = 1
        response_data['message'] = 'Anchor list.'
        response_data['anchor'] = serializer.data
        return JsonResponse(response_data, status=200)
    def post(self,request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        if user:
            # print('&&&&&&&&&&&&&&&&', requestData)
            userAnchorObj = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, id__in=requestData['anchor_ids'])
            # print('&&&&&&&&&&&&&&&&', userAnchorObj)
            serializer = UserAnchorListSerializer(userAnchorObj, many=True)
            response_data['status'] = 1
            response_data['anchor_details'] = serializer.data
            response_data['message'] = 'Request save successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Request save failure.'
            return JsonResponse(response_data, status=200)
    
    def put(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        # print(requestData)
        # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
        set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
        if user.is_superuser == True:
            # print('Super User')
            rs=Anchor.objects.filter(id=requestData['anchor_id']).first()
            if rs:
                # print('########## Anchor Id ############', rs.anchor_id)
                url = str(rs.server_url) + "anchor/reset/?id=" + rs.anchor_id
                # print('########## Anchor Reset Url ############', url)
                result = requests.get(url, headers=set_headers)
                # print('########## Anchor Reset Status Code ############', result.status_code)
                if result.status_code == 200:
                    json_result = result.json()
                    # print('########## Anchor Reset Result JSON ############', json_result)
                    aqs = Anchor.objects.filter(id=requestData['anchor_id']).update(anchor_status='locked', modified_date=timezone.now())
                    userAnchorQS = UserAnchor.objects.filter(anchor_id=requestData['anchor_id']).update(is_deleted=True, is_blocked=True, modified_date=timezone.now())
                    userAnchorRS = UserAnchor.objects.filter(anchor_id=requestData['anchor_id']).first()
                    if userAnchorRS:
                        anchor_coordinate_summery_reset_operations(userAnchorRS.id)
                    response_data['status'] = 1
                    response_data['message'] = 'Anchor reset successfully.'
                    return JsonResponse(response_data, status=200)
                else:   
                    response_data['status'] = 0
                    response_data['message'] = 'Anchor reset failure.'
                    return JsonResponse(response_data, status=200)
        else:
            # print('Not Super User')
            response_data['status'] = 0
            response_data['message'] = 'This user is not admin.'
            return JsonResponse(response_data, status=200)

def anchor_coordinate_summery_operations(operation_type):
    exclude_array = [
        'nats-mum-anchor',
        'nats-blr-anchor',
        'nats-kol-anchor',
        'nats-gwh-anchor',
        'nats-moh-anchor'
    ]
    if operation_type == 'update':
        update_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False).update(regiser_anchor_count=0)
    
    rs_by_country = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False).exclude(anchor_id__anchor_name__in =exclude_array).values('country').annotate(anchor_count=Count('id'))
        
    ##### Start: Create Insert Array Set For GroupWiseAncherLocationLabel #####
    i = 0
    set_array = []
    if rs_by_country:
        for c in rs_by_country:
            rs_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).exclude(anchor_id__anchor_name__in =exclude_array).values_list('id', flat=True)

            rs_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).exclude(anchor_id__anchor_name__in =exclude_array).values_list('latitude', flat=True)

            rs_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).exclude(anchor_id__anchor_name__in =exclude_array).values_list('longitude', flat=True)

            set_array.append(c)
            set_array[i]['parent_id'] = 0
            set_array[i]['user_anchor_ids'] = list(rs_user_anchor_ids)
            set_array[i]['user_anchor_latitude'] = list(rs_user_anchor_latitude)
            set_array[i]['user_anchor_longitude'] = list(rs_user_anchor_longitude)

            rs_by_state = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).exclude(anchor_id__anchor_name__in =exclude_array).values('administrative_area_level_1').annotate(anchor_count=Count('id'))
            
            if rs_by_state:
                j = 0
                set_array[i]['states'] = list(rs_by_state)
                for s in rs_by_state:
                    rs_state_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).exclude(anchor_id__anchor_name__in =exclude_array).values_list('id', flat=True)

                    rs_state_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).exclude(anchor_id__anchor_name__in =exclude_array).values_list('latitude', flat=True)

                    rs_state_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).exclude(anchor_id__anchor_name__in =exclude_array).values_list('longitude', flat=True)   

                    rs_by_city = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values('location').annotate(anchor_count=Count('id'))
                    set_array[i]['states'][j]['parent_id'] = 2
                    set_array[i]['states'][j]['user_anchor_ids'] = list(rs_state_user_anchor_ids)
                    set_array[i]['states'][j]['user_anchor_latitude'] = list(rs_state_user_anchor_latitude)
                    set_array[i]['states'][j]['user_anchor_longitude'] = list(rs_state_user_anchor_longitude)
                    set_array[i]['states'][j]['cities'] = list(rs_by_city)
                    
                    if rs_by_city:
                        k = 0
                        for ct in rs_by_city:
                            rs_city_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).exclude(anchor_id__anchor_name__in =exclude_array).values_list('id', flat=True)

                            rs_city_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).exclude(anchor_id__anchor_name__in =exclude_array).values_list('latitude', flat=True)

                            rs_city_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).exclude(anchor_id__anchor_name__in =exclude_array).values_list('longitude', flat=True)

                            set_array[i]['states'][j]['cities'][k]['parent_id'] = 3
                            set_array[i]['states'][j]['cities'][k]['user_anchor_ids'] = list(rs_city_user_anchor_ids)
                            set_array[i]['states'][j]['cities'][k]['user_anchor_latitude'] = list(rs_city_user_anchor_latitude)
                            set_array[i]['states'][j]['cities'][k]['user_anchor_longitude'] = list(rs_city_user_anchor_longitude)
                            k = k+1
                    j = j+1
            i = i+1
    ##### End: Create Insert Array Set For GroupWiseAncherLocationLabel #####
    if len(set_array) > 0:
        for c in set_array:
            # print('************ Country *************', c)
            country_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, state__isnull=True, city__isnull=True, country=c['country']).count()
            # print('&&&&&&&&&&&&&&&&7 country_rs 7&&&&&&&&&&&&&&&&&', country_rs)
            country_parent_id = 0
            if country_rs == 0:
                central_lat = float(0.00)
                central_lng = float(0.00)
                # print('&&&&&&&&&&&&&&&&7 INSERT RECORD 7&&&&&&&&&&&&&&&&&')
                url = "https://nominatim.openstreetmap.org/?addressdetails=1&q=" + c['country'] +"&format=json&limit=1"
                response = requests.get(url)
                if response.status_code == 200:
                    json_result = response.json()
                    # print(json_result)
                    central_lat = float(json_result[0]["lat"])
                    central_lng = float(json_result[0]["lon"])
                obj = GroupWiseAncherLocationLabel.objects.create(
                    parent_id = 0,
                    label_type = 'country',
                    user_anchor_ids= c['user_anchor_ids'],
                    user_anchor_latitudes= c['user_anchor_latitude'],
                    user_anchor_longitude= c['user_anchor_longitude'],
                    center_latitude= central_lat,
                    center_longitude= central_lng,
                    country= c['country'],
                    regiser_anchor_count=c['anchor_count'],
                    created_date=timezone.now(),
                    modified_date=timezone.now(),
                )
                c['parent_id'] = obj.id
                country_parent_id = obj.id
            else:
                # print('&&&&&&&&&&&&&&&&7 UPDATE RECORD 7&&&&&&&&&&&&&&&&&')
                country_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, state__isnull=True, city__isnull=True, country=c['country']).update(user_anchor_ids= c['user_anchor_ids'], user_anchor_latitudes= c['user_anchor_latitude'], user_anchor_longitude= c['user_anchor_longitude'], regiser_anchor_count=c['anchor_count'])

                rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, state__isnull=True, city__isnull=True, country=c['country']).first()
                country_parent_id = rs.id
            if len(c['states']) > 0:
                for s in c['states']:
                    state_parent_id = 0
                    # print('************ State *************', s)
                    s['parent_id'] = country_parent_id
                    # print('************ State parent_id *************', s['parent_id'])
                    state_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city__isnull=True, country=c['country'], state=s['administrative_area_level_1']).count()
                    if state_rs == 0:
                        # print('&&&&&&&&&&&&&&&&7 INSERT State RECORD 7&&&&&&&&&&&&&&&&&')
                        state_central_lat = float(0.00)
                        state_central_lng = float(0.00)
                        # print('&&&&&&&&&&&&&&&&7 INSERT RECORD 7&&&&&&&&&&&&&&&&&')
                        url = "https://nominatim.openstreetmap.org/?addressdetails=1&q=" + s['administrative_area_level_1'] + "+" + c['country'] + "&format=json&limit=1"
                        response = requests.get(url)
                        if response.status_code == 200:
                            json_result = response.json()
                            # print('State Json', json_result)
                            state_central_lat = float(json_result[0]["lat"])
                            state_central_lng = float(json_result[0]["lon"])

                        stateobj = GroupWiseAncherLocationLabel.objects.create(
                            parent_id = s['parent_id'],
                            label_type = 'state',
                            user_anchor_ids= s['user_anchor_ids'],
                            user_anchor_latitudes= s['user_anchor_latitude'],
                            user_anchor_longitude= s['user_anchor_longitude'],
                            center_latitude= state_central_lat,
                            center_longitude= state_central_lng,
                            country= c['country'],
                            state=s['administrative_area_level_1'],
                            regiser_anchor_count=s['anchor_count'],
                            created_date=timezone.now(),
                            modified_date=timezone.now(),
                        )
                        # s['parent_id'] = stateobj.id
                        state_parent_id = stateobj.id
                    else:
                        # print('&&&&&&&&&&&&&&&&7 Update State RECORD 7&&&&&&&&&&&&&&&&&')
                        state_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city__isnull=True, state=s['administrative_area_level_1'], country=c['country']).update(user_anchor_ids= s['user_anchor_ids'], user_anchor_latitudes= s['user_anchor_latitude'], user_anchor_longitude= s['user_anchor_longitude'], regiser_anchor_count=s['anchor_count'])

                        qs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city__isnull=True, state=s['administrative_area_level_1'], country=c['country']).first()
                        state_parent_id = qs.id

                    if len(s['cities']) > 0:
                        for ct in s['cities']:
                            # print('************ City *************', ct)
                            ct['parent_id'] = state_parent_id
                            # print('************ City  state_parent_id*************', ct['parent_id'])
                            city_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city=ct['location'], country=c['country'], state=s['administrative_area_level_1']).count()
                            city_parent_id = 0
                            if city_rs == 0:
                                # print('&&&&&&&&&&&&&&&&7 INSERT CITY RECORD 7&&&&&&&&&&&&&&&&&')
                                city_central_lat = float(0.00)
                                city_central_lng = float(0.00)
                                # print('&&&&&&&&&&&&&&&&7 INSERT RECORD 7&&&&&&&&&&&&&&&&&')
                                url = "https://nominatim.openstreetmap.org/?addressdetails=1&q=" + ct['location'] + "+" + s['administrative_area_level_1'] + "+" + c['country'] + "&format=json&limit=1"
                                response = requests.get(url)
                                if response.status_code == 200:
                                    json_result = response.json()
                                    # print('State Json', json_result)
                                    if len(json_result) > 0:
                                        city_central_lat = float(json_result[0]["lat"])
                                        city_central_lng = float(json_result[0]["lon"])
                                    else:
                                        city_central_lat = float(ct['user_anchor_latitude'][0])
                                        city_central_lng = float(ct['user_anchor_longitude'][0])

                                cityobj = GroupWiseAncherLocationLabel.objects.create(
                                    parent_id = ct['parent_id'],
                                    label_type = 'city',
                                    user_anchor_ids= ct['user_anchor_ids'],
                                    user_anchor_latitudes= ct['user_anchor_latitude'],
                                    user_anchor_longitude= ct['user_anchor_longitude'],
                                    center_latitude= city_central_lat,
                                    center_longitude= city_central_lng,
                                    country= c['country'],
                                    state=s['administrative_area_level_1'],
                                    city=ct['location'],
                                    regiser_anchor_count=ct['anchor_count'],
                                    created_date=timezone.now(),
                                    modified_date=timezone.now(),
                                )
                                # ct['parent_id'] = cityobj.id
                                city_parent_id = cityobj.id
                            else:
                                # print('&&&&&&&&&&&&&&&&7 Update City RECORD 7&&&&&&&&&&&&&&&&&')
                                city_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city=ct['location'], state=s['administrative_area_level_1'], country=c['country']).update(user_anchor_ids= ct['user_anchor_ids'], user_anchor_latitudes= ct['user_anchor_latitude'], user_anchor_longitude= ct['user_anchor_longitude'], regiser_anchor_count=ct['anchor_count'])

                                cqs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city=ct['location'], state=s['administrative_area_level_1'], country=c['country']).first()
                                ct['parent_id'] = cqs.id
                                city_parent_id = cqs.id



class UserAnchorView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user = request.user
        user_id = user.id
        response_data = {}
        if user.is_superuser == True:
            rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active", anchor_id__is_online=True)
        else:
            rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active", anchor_id__is_online=True).exclude(user_id__is_superuser =True)
        rs = rs.order_by('-id')
        # print(rs.query)
        if rs:
            serializer = UserAnchorSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Anchor list.'
            response_data['anchor'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Anchor list blank.'
            response_data['anchor'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        # print(requestData)
        if user:
            anchorObj = Anchor.objects.filter(is_deleted=False, is_blocked=False, anchor_id=requestData['anchor_id']).first()
            if anchorObj:
                anchorid = anchorObj.id
                obj = UserAnchor.objects.create(
                    anchor_id = anchorid,
                    anchor_qr_code_id = requestData['qr_code_id'],
                    user_id = user_id,
                    lease_id = requestData['lease_id'],
                    aiori_anchor_id = requestData['anchor_id'],
                    lease_from_date= requestData['from_date'],
                    lease_to_date= requestData['to_date'],
                    created_date=timezone.now(),
                    modified_date=timezone.now(),
                )
                AnchorQrCode.objects.filter(id=requestData['qr_code_id']).update(is_registered='yes')
                response_data['status'] = 1
                response_data['message'] = 'User anchor save successfully.'
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'Anchor not found.'
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Request save failure.'
            return JsonResponse(response_data, status=200)

    def put(self,request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        # print('*****************  requestData  ******************', requestData)
        # print(requestData)
        userAnchorObj = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, id=requestData['user_anchor_id']).first()
        if userAnchorObj:
            # obj = UserAnchor.objects.filter(id=requestData['user_anchor_id']).update(location=requestData['location'], latitude=requestData['latitude'], longitude=requestData['longitude'], address=requestData['address'], location_register_status='processing', modified_date=timezone.now())
            obj = UserAnchor.objects.filter(id=requestData['user_anchor_id']).update(latitude=requestData['latitude'],
                                                                                     longitude=requestData['longitude'],
                                                                                     location=requestData['location'],
                                                                                     address=requestData['address'],
                                                                                     sublocality_level_1=requestData['sublocality_level_1'],
                                                                                     sublocality_level_2=requestData['sublocality_level_2'],
                                                                                     sublocality_level_3=requestData['sublocality_level_3'],
                                                                                     administrative_area_level_1=requestData['administrative_area_level_1'],
                                                                                     administrative_area_level_2=requestData['administrative_area_level_2'],
                                                                                     country=requestData['country'],
                                                                                     postal_code =requestData['postal_code'],
                                                                                     modified_date=timezone.now())
            # AnchorQrCode.objects.filter(id=userAnchorObj.anchor_qr_code_id).update(complete_regis='yes')
            anchor_coordinate_summery_operations('update')
            response_data['status'] = 1
            response_data['message'] = 'User anchor update successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Anchor not found.'
            return JsonResponse(response_data, status=200)

        

class UserQrCodeView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user = request.user
        user_id = user.id
        response_data = {}
        rs=AnchorQrCode.objects.filter(user_id=user_id, is_deleted=False).order_by('id')
        if rs:
            serializer = AnchorQrCodeSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'User Anchor list.'
            response_data['lease_anchor'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'User Anchor list blank.'
            response_data['lease_anchor'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        # print(requestData['qr_code'])
        if user:
            return_path = save_qrcode_in_file(requestData['qr_code'])
            if return_path:
             decoded_code = read_qr_code(return_path)
            obj = AnchorQrCode.objects.create(
                    user_id = user_id,
                    anchor_qrcode_file = return_path,
                    decoded_qrcode = decoded_code,
                    created_date=timezone.now(),
                    modified_date=timezone.now(),
                )
            response_data['status'] = 1
            response_data['obj_id'] = 2
            response_data['message'] = 'Request save successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Request save failure.'
            return JsonResponse(response_data, status=200)

class ActiveAnchorNetworkView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):

        try:

            qs = AnchorIpDetails.objects.filter(
                status="online"
            )

            # Remove duplicate IP+ASN
            qs = qs.order_by(
                "ip_address",
                "asn",
                "-updated_at"
            ).distinct("ip_address", "asn")

            print("[NETWORK-API] Unique records:", qs.count())

            if not qs.exists():

                return JsonResponse({
                    "status": 0,
                    "message": "Anchor list blank.",
                    "anchor": []
                }, status=200)

            serializer = ActiveAnchorNetworkSerializer(qs, many=True)

            print("[NETWORK-API] Response rows:", len(serializer.data))

            return JsonResponse({
                "status": 1,
                "message": "Anchor list.",
                "anchor": serializer.data
            }, status=200)

        except Exception as e:

            print("[NETWORK-API] ERROR:", str(e))

            return JsonResponse({
                "status": 0,
                "message": "Internal server error",
                "anchor": []
            }, status=500)
def qrcode_base_lease_request_to_rd3mn(user_anchor_id, lease_id, qr_code, rd3mn_url, anchor_id, rd3mn_anchor_id):
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    response_data = {}
    form_date = date.today()
    fd = form_date.strftime("%Y-%m-%d")
    # print("Today's date:", from_date)
    to_date = date.today() + timedelta(days=365)
    td = to_date.strftime("%Y-%m-%d")
    # print("Today's years date:", to_date)
    # print('&&&& lease_request_to_rd3mn RD3URL &&&&', rd3mn_url)
    url = str(rd3mn_url) + "lease/"
    data = {
        "from_time": fd,
		"to_time": td,
		"lease_id": lease_id,
		"anchor_digest": qr_code
        }
    # print('&&&& lease_request_to_rd3mn Data &&&&', data)
    result = requests.post(url, json=data, headers=set_headers)
    # print('&&&& lease_request_to_rd3mn Result &&&&', result.status_code)
    if result.status_code == 200:
        json_result = result.json()
        # print('############ json_result Show Return ###############', json_result)

        # print('############ json_result Show Return ANCHOR ID ###############', json_result['anchors'])
        useranchorid = user_anchor_id
        anchorid = ''
        rd3mn_anchor_id = ''
        qs = Anchor.objects.filter(anchor_id__in=json_result['anchors'])
        if qs:
            for a in qs:
                anchorid = a.id
                rd3mn_anchor_id = a.anchor_id
        # print('############ Anchor Tables ID ###############', anchorid)
        # print('############ Anchor Tables ANCHOR ID ###############', rd3mn_anchor_id)
        objuseranchor = UserAnchor.objects.filter(id=useranchorid).update(anchor_id=anchorid, aiori_anchor_id=rd3mn_anchor_id, status='accepted', modified_date=timezone.now())

        # print('&&&& lease_request_to_rd3mn return Success &&&&', result.status_code)
        # response_data['status'] = 1                 
        # response_data['message'] = 'RD3MN save successfully.'
        return_data = {
            'status': 1,
            'anchorid': anchorid,
            'rd3mn_anchor_id': rd3mn_anchor_id,
            'rd3mn_url': str(rd3mn_url)
        }
        return return_data
    else:
        # print('&&&& lease_request_to_rd3mn return failure &&&&', result.status_code)
        return 0

def qrcode_base_anchor_location_save_to_rd3mn(rd3mn_anchor_id, latitude, longitude, address, location, administrative_area_level_1, administrative_area_level_2, sublocality_level_1, sublocality_level_2, sublocality_level_3, country, postal_code, user_anchor_id, rd3mn_url):
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    # print('Location Save')
    # print('&&&& anchor_location_save_to_rd3mn RD3URL &&&&', rd3mn_url)
    url = str(rd3mn_url) + "anchor/region/?id=" + rd3mn_anchor_id
    # print('&&&& anchor_location_save_to_rd3mn  Request RD3MN URL &&&&', url)
    locationdata = {
        "latitude": latitude,
		"longitude": longitude
        }
    # print('&&&& anchor_location_save_to_rd3mn Data &&&&', locationdata)
    result = requests.post(url, json=locationdata, headers=set_headers)
    # print('&&&& anchor_location_save_to_rd3mn Result &&&&', result)
    if result.status_code == 200:
        json_result = result.json()
        objlocation = UserAnchor.objects.filter(id=user_anchor_id).update(latitude=latitude, longitude=longitude, location=location, address=address, administrative_area_level_1=administrative_area_level_1, administrative_area_level_2=administrative_area_level_2, sublocality_level_1=sublocality_level_1, sublocality_level_2=sublocality_level_2, sublocality_level_3=sublocality_level_3,
        country=country, postal_code=postal_code, location_register_status='registered', status='active', modified_date=timezone.now())
        # print('&&&& anchor_location_save_to_rd3mn return Success &&&&', result.status_code)
        # response_data['status'] = 1                 
        # response_data['message'] = 'RD3MN location save successfully.'
        return 1
    else:
        # print('&&&& anchor_location_save_to_rd3mn return failure &&&&', result.status_code)
        objlocation = UserAnchor.objects.filter(id=user_anchor_id).update(location_register_status='notregistered', status='accepted', is_blocked=True, is_deleted=True)
        # response_data['status'] = 0                 
        # response_data['message'] = 'RD3MN location could not be received.'
        return 0

class RegisterAnchorView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        user = request.user
        user_id = user.id
        response_data = {}
        rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, user_id=user_id)
        rs = rs.filter(Q(status="accepted") | Q(status="active"))
        rs = rs.order_by('-id')
        # print(rs.query)
        if rs:
            serializer = UserAnchorListSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Anchor list.'
            response_data['lease_anchor'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Anchor list blank.'
            response_data['lease_anchor'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request, *args, **kwargs):
        user = request.user
        user_id = user.id
        response_data = {}
        decoded_code = ''
        requestData = request.data
        # file1 		= request.FILES['file']   		## Uploaded file
        file1 = request.FILES.get('file', None)    ## Uploaded file
        latitude = requestData['lat']
        longitude = requestData['long']
        address = requestData['address']
        location = requestData['location']
        administrative_area_level_1 = requestData['administrative_area_level_1']
        administrative_area_level_2 = requestData['administrative_area_level_2']
        sublocality_level_1 =  requestData['sublocality_level_1']
        sublocality_level_2 = requestData['sublocality_level_2']
        sublocality_level_3 = requestData['sublocality_level_3']
        country = requestData['country']
        postal_code = requestData['postal_code']
        # print('Request Data', requestData)
        if user:
            if file1 is not None:
                # print('FILE HAVE')
                return_path = save_qrcode_file(file1)
                print("RETURN PATH..............................", return_path)
                if return_path:
                    # decoded_code = ''
                    decoded_code = read_qr_code(return_path)
                    print("DECODE CODE..............................", decoded_code)

            if requestData['qr_code']:
                # print('QR CODE HAVE')
                return_path = save_qrcode_in_file(requestData['qr_code'])
                if return_path:
                    decoded_code = requestData['qr_code']
                    # decoded_code = read_qr_code(return_path)
            # print('&&&&&&&& Decoded QR Code &&&&&&&&&', decoded_code)
            if decoded_code:
                # chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
                chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
                lease_id = get_random_string(50, chars)
                obj = UserAnchor.objects.create(
                    # anchor_id = anchorid,
                    # anchor_qr_code_id = requestData['qr_code_id'],
                    user_id = user_id,
                    lease_id = lease_id,
                    # aiori_anchor_id = requestData['anchor_id'],
                    anchor_qrcode_file= return_path,
                    decoded_qrcode= decoded_code,
                    lease_from_date= requestData['date_from'],
                    lease_to_date= requestData['date_to'],
                    created_date=timezone.now(),
                    modified_date=timezone.now(),
                )
                rd3mn_url = 'https://apird3v0.aior.in/apisrv/api/v1/'
                return_result = qrcode_base_lease_request_to_rd3mn(obj.id, obj.lease_id, obj.decoded_qrcode, rd3mn_url, '', '')
                # print('###### After lease request Save Return Result ############', return_result)
                # print('###### After lease request Save Return Result Status ############', return_result['status'])
                if return_result['status'] == 1:
                    locationRegisterResult = qrcode_base_anchor_location_save_to_rd3mn(return_result['rd3mn_anchor_id'], latitude, longitude, address, location, administrative_area_level_1, administrative_area_level_2, sublocality_level_1, sublocality_level_2, sublocality_level_3, country, postal_code, obj.id, rd3mn_url)
                    if locationRegisterResult == 1:
                        anchor_coordinate_summery_operations('insert')
                        response_data['status'] = 1
                        response_data['id'] = obj.id
                        response_data['lease_id'] = obj.lease_id
                        response_data['qr_code'] = obj.decoded_qrcode
                        response_data['message'] = 'Request save successfully.'
                        return JsonResponse(response_data, status=200)
                    else:
                        # print(locationRegisterResult)
                        response_data['status'] = 0
                        response_data['message'] = 'Location is not register in RD3MN server.'
                        return JsonResponse(response_data, status=200) 
            else:
                response_data['status'] = 0
                response_data['lease_id'] = ''
                response_data['message'] = 'QR Code not decoded.'
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Request save failure.'
            return JsonResponse(response_data, status=200)

    def put(self,request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        # print(requestData)
        if user:
            anchorObj = Anchor.objects.filter(is_deleted=False, is_blocked=False, anchor_id=requestData['anchor_id']).first()
            if anchorObj:
                anchorid = anchorObj.id
                obj = UserAnchor.objects.filter(id=requestData['user_anchor_id']).update(anchor_id=anchorid, aiori_anchor_id=requestData['anchor_id'], status='accepted', modified_date=timezone.now())
                response_data['status'] = 1
                response_data['message'] = 'User anchor update successfully.'
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'Anchor not found.'
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Request update failure.'
            return JsonResponse(response_data, status=200)


class RegisterAnchorDetailsView(APIView):
    permission_classes = (IsAuthenticated,)

    # def get(self,request):
    #     user = request.user
    #     user_id = user.id
    #     response_data = {}
    #     rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, user_id=user_id)
    #     rs = rs.filter(Q(status="accepted") | Q(status="active"))
    #     rs = rs.order_by('-id')
    #     print(rs.query)
    #     if rs:
    #         serializer = UserAnchorListSerializer(rs, many=True)
    #         response_data['status'] = 1
    #         response_data['message'] = 'Anchor list.'
    #         response_data['lease_anchor'] = serializer.data
    #         return JsonResponse(response_data, status=200)
    #     else:
    #         response_data['status'] = 0
    #         response_data['message'] = 'Anchor list blank.'
    #         response_data['lease_anchor'] = []
    #         return JsonResponse(response_data, status=200)

    def post(self, request, *args, **kwargs):
        user = request.user
        user_id = user.id
        response_data = {}
        # anchor_id = request.data.get('anchor_id', None)
        requestData = request.data
        # print('Request Data', requestData)
        if user:
            if requestData['anchor_id'] == 'all':
                rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, user_id=user_id, status="active")
                if rs:
                    serializer = UserAnchorListSerializer(rs, many=True)
                    response_data['status'] = 1
                    response_data['message'] = 'Anchor details.'
                    response_data['anchor_details'] = serializer.data
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Anchor details.'
                    response_data['anchor_details'] = []
                    return JsonResponse(response_data, status=200)
            else:
                # rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, id=anchor_id, user_id=user_id, status="active", lease_to_date__gte=timezone.now()).first()
                rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, id=requestData['anchor_id'], user_id=user_id, status="active").first()
                if rs:
                    serializer = UserAnchorListSerializer(rs)
                    response_data['status'] = 1
                    response_data['message'] = 'Anchor details.'
                    response_data['anchor_details'] = serializer.data
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Anchor details.'
                    response_data['anchor_details'] = []
                    return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Request save failure.'
            return JsonResponse(response_data, status=200)

    def put(self,request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        # print(requestData)
        userAnchorObj = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, id=requestData['user_anchor_id']).first()
        if userAnchorObj:
            obj = UserAnchor.objects.filter(id=requestData['user_anchor_id']).update(location=requestData['location'], status=requestData['anchor_status'], location_register_status=requestData['location_status'], modified_date=timezone.now())
            # AnchorQrCode.objects.filter(id=userAnchorObj.anchor_qr_code_id).update(complete_regis='yes')
            response_data['status'] = 1
            response_data['message'] = 'User anchor update successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Anchor not found.'
            return JsonResponse(response_data, status=200)

# def SaveAnchorDetailsFromAIORICronClass():
#     print("CRON2")
#     response_data = {}
#     # query = str(settings.AIORI_DEVICE_ANCHOR_HOST) + ":" + str(settings.AIORI_DEVICE_ANCHOR_PORT) + str(settings.AIORI_DEVICE_ANCHOR_URL) + "anchor/?limit=100"
#     query = str(settings.AIORI_ANCHOR_HOST) + str(settings.AIORI_ANCHOR_URL) + "anchor/?limit=100"
#     # print(query)
#     result = requests.get(query)
#     if result.status_code == 200:
#         json_result = result.json()
#         for value in json_result:
#             print('&&&&&&&& Anchor Details &&&&&&&&', value)
#             rs=Anchor.objects.filter(anchor_id=value['id']).first()
#             if rs:
#                 ## Update Record In Anchor Table
#                 Anchor.objects.filter(id=rs.id).update(
#                     anchor_name = value['name'],
#                     anchor_id=value['id'],
#                     is_active=value['is_active'],
#                     is_online=value['is_online'],
#                     anchor_status=value['status'],
#                     anchor_created_date=value['created_date'],
#                     anchor_updated_at=value['updated_at'],
#                     modified_date=timezone.now(),
#                 )
#             else:
#                 ## Insert Record In Anchor Table
#                 obj = Anchor.objects.create(
#                     # anchor_name = get_random_string(8,'0123456789'),
#                     anchor_name = value['name'],
#                     anchor_id=value['id'],
#                     is_active=value['is_active'],
#                     is_online=value['is_online'],
#                     anchor_status=value['status'],
#                     anchor_created_date=value['created_date'],
#                     anchor_updated_at=value['updated_at'],
#                     created_date=timezone.now(),
#                     modified_date=timezone.now(),
#               )

def UserLeaseAnchorResetCron():
    # print('UserLeaseAnchorResetCron')
    userAnchorQs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status='active', location_register_status='registered')
    if userAnchorQs:
        for useranchor in userAnchorQs:
            anchor_rs = Anchor.objects.filter(id=useranchor.anchor_id).first()
            if anchor_rs:
                if anchor_rs.anchor_status == 'locked':
                    userAnchorQs = UserAnchor.objects.filter(id=useranchor.id).update(is_deleted=True, is_blocked=True)
                    print('User anchor id: ', useranchor.id, ' is update')
                else:
                    print('anchar status is: ', anchor_rs.anchor_status)
            else:
                print('anchor is not present.')



def SaveAnchorDetailsFromAIORICronClass():
    #print("CRON2")
    # response_data = {}
    # geting_urls = settings.AIORI_ANCHOR_HOST_URLS
    # range_limit = int(settings.AIORI_ANCHOR_GET_RANGE_LIMIT)
    # print(geting_urls)
    # a = []
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    # set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    # for url in geting_urls:
    #     a.append(url)
    #     print(url['server_url'])
    #     print(url['storage_url'])
    #     print(url['storage_db'])
    #     print(url['version'])
    #     #### NEW CODE APPEND ####
    #     skip = 0
    #     limit = 10
    #     for i in range(range_limit):
    #         # query = str(url['server_url']) + "anchor/?limit=500"
    #         # print(query)
    #         query = str(url['server_url']) + "anchor/?skip="+str(skip)+"&limit="+str(limit)
    #         print(query)
    #         result = requests.get(query, headers=set_headers)
    #         if result.status_code == 200:
    #             json_result = result.json()
    #             if len(json_result) > 0:
    #                 for value in json_result:
    #                     print('&&&&&&&& Anchor Details &&&&&&&&', value)
    #                     rs=Anchor.objects.filter(anchor_id=value['id']).first()
    #                     if rs:
    #                         ## Update Record In Anchor Table
    #                         Anchor.objects.filter(id=rs.id).update(
    #                             # anchor_name = value['name'],
    #                             # anchor_id=value['id'],
    #                             # is_active=value['is_active'],
    #                             # server_url = url['server_url'],
    #                             # db_url = url['storage_url'],
    #                             # storage_db = url['storage_db'],
    #                             # version = url['version'],
    #                             is_online=value['is_online'],
    #                             anchor_status=value['status'],
    #                             # anchor_created_date=value['created_date'],
    #                             # anchor_updated_at=value['updated_at'],
    #                             modified_date=timezone.now(),
    #                         )
    #                     else:
    #                         ## Insert Record In Anchor Table
    #                         obj = Anchor.objects.create(
    #                             # anchor_name = get_random_string(8,'0123456789'),
    #                             anchor_name = value['name'],
    #                             anchor_id=value['id'],
    #                             # is_active=value['is_active'],
    #                             server_url = url['server_url'],
    #                             db_url = url['storage_url'],
    #                             storage_db = url['storage_db'],
    #                             version = url['version'],
    #                             is_online=value['is_online'],
    #                             anchor_status=value['status'],
    #                             anchor_created_date=value['created_date'],
    #                             anchor_updated_at=value['updated_at'],
    #                             created_date=timezone.now(),
    #                             modified_date=timezone.now(),
    #                         )
    #         skip = skip + 10
    #         limit = limit + 10
    #         print('########## FOR LOOP RANGE ############', i)
    #         print('########## FOR LOOP RANGE SKIP ############', skip)
    #         print('########## FOR LOOP RANGE LIMIT ############', limit)

    response_data = {}
    geting_urls = settings.AIORI_ANCHOR_HOST_URLS_TEST
    range_limit = int(settings.AIORI_ANCHOR_GET_RANGE_LIMIT)
    aiori_server_url = str(settings.AIORI_ANCHOR_SERVER_URLS)
    # print(geting_urls)
    rd3anchor_details = []
    anchor_ids = []
    insert_array = []
    update_array = []
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    rs = Anchor.objects.filter(is_blocked=False, is_deleted=False, version=1)
    # rs = rs.filter(Q(anchor_status='active') | Q(anchor_status='requested'))
    rs = rs.values('id', 'anchor_id', 'is_online', 'anchor_name', 'anchor_status')
    if rs:
        for a in rs:
            anchor_ids.append(a['anchor_id'])
        skip = 0
        limit = 20
        for i in range(range_limit):
            query = aiori_server_url + "anchor/?skip="+str(skip)+"&limit="+str(limit)
            #print(query)
            result = requests.get(query,headers=set_headers)
            #print('result.status_code &&&&&&&&&&&&&&&&&&', result.status_code)
            if result.status_code == 200:
                json_result = result.json()
                if len(json_result) > 0:
                    # print('&&&&&&&& Anchor Details &&&&&&&&', json_result)
                    for value in json_result:
                        rd3anchor_details.append(value)
            skip = skip + 20
            limit = limit + 20
            # print('########## FOR LOOP RANGE ############', i)
            # print('########## FOR LOOP RANGE SKIP ############', skip)
            # print('########## FOR LOOP RANGE LIMIT ############', limit)
        if len(rd3anchor_details) > 0:
            for n in rd3anchor_details:
                if n['id'] not in anchor_ids:
                    insert_array.append(n)
                else:
                    for x in rs:
                        if n['id'] == x['anchor_id']:
                            if n['is_online'] != x['is_online']:
                                x['is_online'] = n['is_online']
                                x['anchor_status'] = n['status']
                                update_array.append(x)

            # Bulk Update Records
            if len(update_array) > 0:
                for value in update_array:
                    Anchor.objects.filter(pk=value['id']).update(
                            is_online=value['is_online'],
                            anchor_status=value['anchor_status'],
                            modified_date=timezone.now(),
                        )
                    # print('########## Update Anchor ############', value['anchor_name'])
            # Bulk Create Records
            if len(update_array) > 0:
                for value in insert_array:
                    obj = Anchor.objects.create(
                            anchor_name = value['name'],
                            anchor_id=value['id'],
                            server_url = 'https://apird3v0.aior.in/apisrv/api/v1/',
                            db_url = 'https://pingdb.v0.aior.in',
                            storage_db = 'pingdb',
                            version = 1,
                            is_online=value['is_online'],
                            anchor_status=value['status'],
                            anchor_created_date=value['created_date'],
                            anchor_updated_at=value['updated_at'],
                            created_date=timezone.now(),
                            modified_date=timezone.now(),
                        )
                    print('########## Insert Anchor ############', value['name'])

class AnchorUpdate(APIView):
    def get(self,request):
        response_data = {}
        geting_urls = settings.AIORI_ANCHOR_HOST_URLS_TEST
        range_limit = int(settings.AIORI_ANCHOR_GET_RANGE_LIMIT)
        aiori_server_url = str(settings.AIORI_ANCHOR_SERVER_URLS)
        # print(geting_urls)
        rd3anchor_details = []
        anchor_ids = []
        insert_array = []
        update_array = []
        # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
        set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
        rs = Anchor.objects.filter(is_blocked=False, is_deleted=False, version=1)
        # rs = rs.filter(Q(anchor_status='active') | Q(anchor_status='requested'))
        rs = rs.values('id', 'anchor_id', 'is_online', 'anchor_name', 'anchor_status')
        if rs:
            for a in rs:
                anchor_ids.append(a['anchor_id'])
            skip = 0
            limit = 20
            for i in range(range_limit):
                query = aiori_server_url + "anchor/?skip="+str(skip)+"&limit="+str(limit)
                # print(query)
                result = requests.get(query,headers=set_headers)
                # print('result.status_code &&&&&&&&&&&&&&&&&&', result.status_code)
                if result.status_code == 200:
                    json_result = result.json()
                    if len(json_result) > 0:
                        # print('&&&&&&&& Anchor Details &&&&&&&&', json_result)
                        for value in json_result:
                            rd3anchor_details.append(value)
                skip = skip + 20
                limit = limit + 20
                # print('########## FOR LOOP RANGE ############', i)
                # print('########## FOR LOOP RANGE SKIP ############', skip)
                # print('########## FOR LOOP RANGE LIMIT ############', limit)
            if len(rd3anchor_details) > 0:
                for n in rd3anchor_details:
                    if n['id'] not in anchor_ids:
                        insert_array.append(n)
                    else:
                        for x in rs:
                            if n['id'] == x['anchor_id']:
                                if n['is_online'] != x['is_online']:
                                    x['is_online'] = n['is_online']
                                    x['anchor_status'] = n['status']
                                    update_array.append(x)

                # Bulk Update Records
                if len(update_array) > 0:
                    for value in update_array:
                       Anchor.objects.filter(pk=value['id']).update(
                                is_online=value['is_online'],
                                anchor_status=value['anchor_status'],
                                modified_date=timezone.now(),
                            )
                # Bulk Create Records
                if len(update_array) > 0:
                    for value in insert_array:
                        obj = Anchor.objects.create(
                                anchor_name = value['name'],
                                anchor_id=value['id'],
                                server_url = 'https://apird3v0.aior.in/apisrv/api/v1/',
                                db_url = 'https://pingdb.v0.aior.in',
                                storage_db = 'pingdb',
                                version = 1,
                                is_online=value['is_online'],
                                anchor_status=value['status'],
                                anchor_created_date=value['created_date'],
                                anchor_updated_at=value['updated_at'],
                                created_date=timezone.now(),
                                modified_date=timezone.now(),
                            )
            
            response_data['status'] = 1
            response_data['message'] = 'Anchor list.'
            # response_data['lease_anchor'] = list(rs)
            # response_data['V1-anchor'] = rd3anchor_details
            response_data['anchor_ids'] = anchor_ids
            response_data['insert_array'] = insert_array
            response_data['update_array'] = update_array
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 1
            response_data['message'] = 'Anchor list blank.'
            return JsonResponse(response_data, status=200)
        # for url in geting_urls:
        #     a.append(url)
        #     print(url['server_url'])
        #     print(url['storage_url'])
        #     print(url['storage_db'])
        #     print(url['version'])
            # query = str(url['server_url']) + "anchor/?limit=500"
            # print(query)
            # result = requests.get(query,headers=set_headers)
            # print('result.status_code &&&&&&&&&&&&&&&&&&', result.status_code)

            #### NEW CODE APPEND ####
            # skip = 0
            # limit = 10
            # for i in range(range_limit):
            #     query = str(url['server_url']) + "anchor/?skip="+str(skip)+"&limit="+str(limit)
            #     print(query)
            #     result = requests.get(query,headers=set_headers)
            #     print('result.status_code &&&&&&&&&&&&&&&&&&', result.status_code)
            #     if result.status_code == 200:
            #         json_result = result.json()
            #         if len(json_result) > 0:
            #             for value in json_result:
            #                 print('&&&&&&&& Anchor Details &&&&&&&&', value)
            #                 if url['version'] == 0:
            #                     v0.append(value)
            #                 if url['version'] == 1:
            #                     v1.append(value)
            #                 # rs=Anchor.objects.filter(anchor_id=value['id']).first()
            #                 # if rs:
            #                 #     ## Update Record In Anchor Table
            #                 #     Anchor.objects.filter(id=rs.id).update(
            #                 #         # anchor_name = value['name'],
            #                 #         # anchor_id=value['id'],
            #                 #         # is_active=value['is_active'],
            #                 #         server_url = url['server_url'],
            #                 #         db_url = url['storage_url'],
            #                 #         storage_db = url['storage_db'],
            #                 #         version = url['version'],
            #                 #         is_online=value['is_online'],
            #                 #         anchor_status=value['status'],
            #                 #         # anchor_created_date=value['created_date'],
            #                 #         # anchor_updated_at=value['updated_at'],
            #                 #         modified_date=timezone.now(),
            #                 #     )
            #                 # else:
            #                 #     ## Insert Record In Anchor Table
            #                 #     obj = Anchor.objects.create(
            #                 #         # anchor_name = get_random_string(8,'0123456789'),
            #                 #         anchor_name = value['name'],
            #                 #         anchor_id=value['id'],
            #                 #         # is_active=value['is_active'],
            #                 #         server_url = url['server_url'],
            #                 #         db_url = url['storage_url'],
            #                 #         storage_db = url['storage_db'],
            #                 #         version = url['version'],
            #                 #         is_online=value['is_online'],
            #                 #         anchor_status=value['status'],
            #                 #         anchor_created_date=value['created_date'],
            #                 #         anchor_updated_at=value['updated_at'],
            #                 #         created_date=timezone.now(),
            #                 #         modified_date=timezone.now(),
            #                 #     )
                # skip = skip + 10
                # limit = limit + 10
            #     print('########## FOR LOOP RANGE ############', i)
            #     print('########## FOR LOOP RANGE SKIP ############', skip)
            #     print('########## FOR LOOP RANGE LIMIT ############', limit)

        # response_data['status'] = 1
        # response_data['message'] = 'Anchor list blank.'
        # response_data['lease_anchor'] = a
        # response_data['V0-anchors'] = v0
        # response_data['V1-anchor'] = v1
        # return JsonResponse(response_data, status=200)


class AnchorIpDetailsUpdate(APIView):
    def get(self,request):
        import urllib, json
        response_data = {}
        ### Ip Address Validation Checking Dated On 07-04-2022
        # userAnchorQs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status='active', location_register_status='registered', administrative_area_level_2__isnull=True)
        # userAnchorQs = userAnchorQs.order_by('id')
        # userAnchorQs = userAnchorQs.values('id', 'anchor_id__anchor_name', 'user_id__first_name')
        # response_data['status'] = 1
        # response_data['message'] = 'Anchor list blank.'
        # response_data['data'] = list(userAnchorQs)
        # return JsonResponse(response_data, status=200)
        ### Ip Address Validation Checking Dated On 07-04-2022
        aiori_server_url = str(settings.AIORI_ANCHOR_SERVER_URLS)
        anchor_ids = []
        insert_array = []
        update_array = []
        ip_type = 'v4'
        ip_v6 = 'no'
        localhost_ipv6 = '::1'
        set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
        # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
        rs = Anchor.objects.filter(is_blocked=False, is_deleted=False, version=1)
        rs = rs.values('id', 'anchor_id')
        rs = rs.order_by('id')
        if rs:
            for i in rs:
                query = aiori_server_url + "anchor/pubip/?id="+str(i['anchor_id'])
                # print(query)
                result = requests.get(query,headers=set_headers)
                print('result.status_code &&&&&&&&&&&&&&&&&&', result.status_code)
                if result.status_code == 200:
                    json_result = result.json()
                    if len(json_result) > 0:
                        # print('&&&&&&&& Anchor Details &&&&&&&&', json_result)
                        if 'ipv6' in json_result:
                            print('&&&&&&&& Anchor IP V6 Details &&&&&&&&', json_result['ipv6'])
                            if json_result['ipv6'] == '::1':
                                ip_type = 'v4'
                                ip_v6 = json_result['ipv6']
                            else:
                                ip_type = 'v6'
                                ip_v6 = json_result['ipv6']
                        else:
                            ip_type = 'v4'
                            ip_v6 = 'no'
                        json_result['iptype'] = ip_type
                        json_result['ip_v6'] = ip_v6
                        insert_array.append(json_result)
                        # for value in json_result:
                        #     rd3anchor_details.append(value)
                print('########## FOR LOOP RANGE ############', i)

            # Bulk Update Records
            # if len(insert_array) > 0:
            #     for value in insert_array:
            #         Anchor.objects.filter(anchor_id=value['id']).update(
            #                 ip_type=value['iptype'],
            #                 public_ip=value['pubip'],
            #                 ip_v6=value['ip_v6']
            #             )
            
            response_data['status'] = 1
            response_data['message'] = 'Anchor list.'
            response_data['lease_anchor'] = list(rs)
            # response_data['V1-anchor'] = rd3anchor_details
            response_data['anchor_ids'] = anchor_ids
            response_data['insert_array'] = insert_array
            response_data['update_array'] = update_array
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 1
            response_data['message'] = 'Anchor list blank.'
            return JsonResponse(response_data, status=200)

def lease_request_to_rd3mn(user_anchor_id, lease_id, qr_code, rd3mn_url, anchor_id, rd3mn_anchor_id):
    set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    response_data = {}
    form_date = date.today()
    fd = form_date.strftime("%Y-%m-%d")
    # print("Today's date:", from_date)
    to_date = date.today() + timedelta(days=365)
    td = to_date.strftime("%Y-%m-%d")
    # print("Today's years date:", to_date)
    # print('&&&& lease_request_to_rd3mn RD3URL &&&&', rd3mn_url)
    url = str(rd3mn_url) + "lease/"
    data = {
        "from_time": fd,
		"to_time": td,
		"lease_id": lease_id,
		"anchor_digest": qr_code
        }
    # print('&&&& lease_request_to_rd3mn Data &&&&', data)
    result = requests.post(url, json=data, headers=set_headers)
    # print('&&&& lease_request_to_rd3mn Result &&&&', result.status_code)
    if result.status_code == 200:
        json_result = result.json()
        useranchorid = user_anchor_id
        anchorid = anchor_id
        rd3mn_anchor_id = rd3mn_anchor_id
        objuseranchor = UserAnchor.objects.filter(id=useranchorid).update(anchor_id=anchorid, aiori_anchor_id=rd3mn_anchor_id, status='accepted', modified_date=timezone.now())
        # print('&&&& lease_request_to_rd3mn return Success &&&&', result.status_code)
        # response_data['status'] = 1                 
        # response_data['message'] = 'RD3MN save successfully.'
        return 1
    else:
        # print('&&&& lease_request_to_rd3mn return failure &&&&', result.status_code)
        return 0

def anchor_location_save_to_rd3mn(rd3mn_anchor_id, latitude, longitude, address, location, user_anchor_id, rd3mn_url):
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    # print('Location Save')
    # print('&&&& anchor_location_save_to_rd3mn RD3URL &&&&', rd3mn_url)
    url = str(rd3mn_url) + "anchor/region/?id=" + rd3mn_anchor_id
    # print('&&&& anchor_location_save_to_rd3mn  Request RD3MN URL &&&&', url)
    locationdata = {
        "latitude": latitude,
		"longitude": longitude
        }
    # print('&&&& anchor_location_save_to_rd3mn Data &&&&', locationdata)
    result = requests.post(url, json=locationdata, headers=set_headers)
    # print('&&&& anchor_location_save_to_rd3mn Result &&&&', result)
    if result.status_code == 200:
        json_result = result.json()
        objlocation = UserAnchor.objects.filter(id=user_anchor_id).update(latitude=latitude, longitude=longitude, location=location, address=address, location_register_status='registered', status='active', modified_date=timezone.now())
        print('&&&& anchor_location_save_to_rd3mn return Success &&&&', result.status_code)
        # response_data['status'] = 1                 
        # response_data['message'] = 'RD3MN location save successfully.'
        return 1
    else:
        print('&&&& anchor_location_save_to_rd3mn return failure &&&&', result.status_code)
        objlocation = UserAnchor.objects.filter(id=user_anchor_id).update(location_register_status='notregistered', status='accepted', is_blocked=True, is_deleted=True)
        # response_data['status'] = 0                 
        # response_data['message'] = 'RD3MN location could not be received.'
        return 0

class LeaseAnchorByAnchorNameView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request, *args, **kwargs):
        user = request.user
        user_id = user.id
        response_data = {}
        decoded_code = ''
        requestData = request.data
        # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
        set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
        form_date = date.today()
        to_date = date.today() + timedelta(days=365)

        if user:
            rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active", location_register_status='registered', anchor_id__anchor_name=requestData['anchor_name'].upper())
            rs = rs.filter(Q(anchor_id__anchor_status='active') | Q(anchor_id__anchor_status='requested'))
            # rs = rs.values('id', 'anchor_id__anchor_id')
            # rs = rs.first()
            print('################',rs.count())
            # response_data['status'] = 0
            # response_data['lease_id'] = ''
            # response_data['message'] = 'It has been registered for someone else.'
            # return JsonResponse(response_data, status=200)
            if rs.count() == 0:
                anchor_rs = Anchor.objects.filter(is_deleted=False, is_blocked=False, anchor_name=requestData['anchor_name'].upper(), anchor_status='locked')
                # anchor_rs = Anchor.objects.filter(is_deleted=False, is_blocked=False, anchor_name=requestData['anchor_name'].upper())
                anchor_rs = anchor_rs.values('id', 'anchor_id', 'server_url')
                anchor_rs = anchor_rs.first()
                # print('&&&&&&&&&&&&&&&&&& json_result &&&&&&&&&&&&&&', anchor_rs['anchor_id'])
                if anchor_rs:
                    query = str(anchor_rs['server_url']) + "anchor/get/" + anchor_rs['anchor_id']
                    result = requests.get(query,headers=set_headers)
                    if result.status_code == 200:
                        json_result = result.json()
                        # print('&&&&&&&&&&&&&&&&&& json_result &&&&&&&&&&&&&&', json_result['qr_code'])
                        if json_result['qr_code']:
                                return_path = save_qrcode_in_file(json_result['qr_code'])
                                if return_path:
                                    decoded_code = read_qr_code(return_path)
                                if decoded_code:
                                    # chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
                                    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
                                    lease_id = get_random_string(50, chars)
                                    obj = UserAnchor.objects.create(
                                        user_id = user_id,
                                        lease_id = lease_id,
                                        anchor_qrcode_file= return_path,
                                        decoded_qrcode= decoded_code,
                                        lease_from_date= form_date,
                                        lease_to_date= to_date,
                                        created_date=timezone.now(),
                                        modified_date=timezone.now(),
                                    )
                                    return_result = lease_request_to_rd3mn(obj.id, lease_id, decoded_code, anchor_rs['server_url'], anchor_rs['id'], anchor_rs['anchor_id'])
                                    if return_result == 1:
                                        # print('&&&&&&&&&&&&&&7 Save Result &&&&&&&&&&&&&&&&&', return_result)
                                        locationRegisterResult = anchor_location_save_to_rd3mn(anchor_rs['anchor_id'], requestData['lat'], requestData['long'], requestData['address'], requestData['location'], obj.id, anchor_rs['server_url'])
                                        if locationRegisterResult == 1:
                                            response_data['status'] = 1
                                            # response_data['id'] = obj.id
                                            response_data['lease_id'] = lease_id
                                            # response_data['qr_code'] = obj.decoded_qrcode
                                            response_data['message'] = 'Request save successfully.'
                                            return JsonResponse(response_data, status=200)
                                        else:
                                            # print(locationRegisterResult)
                                            response_data['status'] = 0
                                            response_data['message'] = 'Location is not register in RD3MN server.'
                                            return JsonResponse(response_data, status=200) 
                                    else:
                                        # print(return_result)
                                        response_data['status'] = 0
                                        response_data['message'] = 'Anchor is not register in RD3MN server.'
                                        return JsonResponse(response_data, status=200)
                                else:
                                    response_data['status'] = 1
                                    response_data['id'] = rs.count()
                                    # response_data['lease_id'] = obj.lease_id
                                    response_data['qr_code'] = json_result['qr_code']
                                    response_data['message'] = 'Request save successfully.'
                                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'It has been registered for someone else.'
                    return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['lease_id'] = ''
                response_data['message'] = 'It has been registered for someone else.'
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Request save failure.'
            return JsonResponse(response_data, status=200)

class LocationWiseUserAnchorView(APIView):
    # permission_classes = (IsAuthenticated,)
    def get(self,request):
        import requests
        import urllib.parse
        user = request.user
        user_id = user.id
        response_data = {}
        rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active", anchor_id__is_online=True).exclude(user_id__is_superuser =True).values('location').annotate(count=Count('id'))
        # rs = rs.order_by('-id')
        # print(rs)
        if rs:
            for r in rs:
                if r['location']:
                    nods = {}
                    print(r['location'])
                    city = r['location']
                    # country = "France"
                    # url = "https://nominatim.openstreetmap.org/?addressdetails=1&q=" + city + "+" + country +"&format=json&limit=1"
                    url = "https://nominatim.openstreetmap.org/?addressdetails=1&q=" + city +"&format=json&limit=1"
                    response = requests.get(url)
                    # print(response[0]["lat"])
                    # print(response[0]["lon"])
                    # nods = {
                    #     'location': r['location'],
                    #     "count"
                    # }
                    if response.status_code == 200:
                        json_result = response.json()
                        # print(json_result)
                        r['lat'] = float(json_result[0]["lat"])
                        r['long'] = float(json_result[0]["lon"])
            serializer = UserAnchorGroupBySerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Anchor list.'
            # response_data['anchor'] = serializer.data
            response_data['anchor'] = list(rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Anchor list blank.'
            response_data['anchor'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        import requests
        import urllib.parse
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        # print(requestData)
        # UserAnchor.objects.filter(location__isnull=False, address__isnull=False).update(country='India')

        # rs_by_record = UserAnchor.objects.filter(id=201).first()

        # rs_by_country = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=rs_by_record.country).values('country').annotate(anchor_count=Count('id'))
        
        #### Start: Create Insert Array Set For GroupWiseAncherLocationLabel #####
        # rs_by_country = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False).values('country').annotate(anchor_count=Count('id'))
        # i = 0
        # set_array = []
        # if rs_by_country:
        #     for c in rs_by_country:
        #         rs_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('id', flat=True)

        #         rs_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('latitude', flat=True)

        #         rs_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('longitude', flat=True)

        #         set_array.append(c)
        #         set_array[i]['parent_id'] = 1
        #         set_array[i]['user_anchor_ids'] = list(rs_user_anchor_ids)
        #         set_array[i]['user_anchor_latitude'] = list(rs_user_anchor_latitude)
        #         set_array[i]['user_anchor_longitude'] = list(rs_user_anchor_longitude)

        #         rs_by_state = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1__isnull=False).values('administrative_area_level_1').annotate(anchor_count=Count('id'))
               
        #         if rs_by_state:
        #             j = 0
        #             set_array[i]['states'] = list(rs_by_state)
        #             for s in rs_by_state:
        #                 rs_state_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, administrative_area_level_1=s['administrative_area_level_1'], country=c['country']).values_list('id', flat=True)

        #                 rs_state_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1=s['administrative_area_level_1'], location__isnull=False, address__isnull=False, country=c['country']).values_list('latitude', flat=True)

        #                 rs_state_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1=s['administrative_area_level_1'], location__isnull=False, address__isnull=False, country=c['country']).values_list('longitude', flat=True)   

        #                 rs_by_city = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, administrative_area_level_1=s['administrative_area_level_1'], address__isnull=False, country=c['country'], location__isnull=False).values('location').annotate(anchor_count=Count('id'))
        #                 set_array[i]['states'][j]['parent_id'] = 2
        #                 set_array[i]['states'][j]['user_anchor_ids'] = list(rs_state_user_anchor_ids)
        #                 set_array[i]['states'][j]['user_anchor_latitude'] = list(rs_state_user_anchor_latitude)
        #                 set_array[i]['states'][j]['user_anchor_longitude'] = list(rs_state_user_anchor_longitude)
        #                 # set_array[i]['states'][j]['cities'] = list(rs_by_city)
                        
        #                 if rs_by_city:
        #                     k = 0
        #                     set_array[i]['states'][j]['cities'] = list(rs_by_city)
        #                     for ct in rs_by_city:
        #                         rs_city_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('id', flat=True)

        #                         rs_city_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('latitude', flat=True)

        #                         rs_city_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('longitude', flat=True)

        #                         set_array[i]['states'][j]['cities'][k]['parent_id'] = 2
        #                         set_array[i]['states'][j]['cities'][k]['user_anchor_ids'] = list(rs_city_user_anchor_ids)
        #                         set_array[i]['states'][j]['cities'][k]['user_anchor_latitude'] = list(rs_city_user_anchor_latitude)
        #                         set_array[i]['states'][j]['cities'][k]['user_anchor_longitude'] = list(rs_city_user_anchor_longitude)
        #                         k = k+1
        #                 j = j+1
        #         i = i+1
        ##### End: Create Insert Array Set For GroupWiseAncherLocationLabel #####


        ##### Start: Create Update Array Set For GroupWiseAncherLocationLabel #####
        # rs_update = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, id=197).first()
        # update_set_array = []
        # if rs_update:
        #     rs_by_country = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=rs_update.country).values('country').annotate(anchor_count=Count('id'))
        #     if rs_by_country:
        #         i = 0
        #         for c in rs_by_country:
        #             rs_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('id', flat=True)

        #             rs_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('latitude', flat=True)

        #             rs_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('longitude', flat=True)

        #             update_set_array.append(c)
        #             update_set_array[i]['parent_id'] = 1
        #             update_set_array[i]['user_anchor_ids'] = list(rs_user_anchor_ids)
        #             update_set_array[i]['user_anchor_latitude'] = list(rs_user_anchor_latitude)
        #             update_set_array[i]['user_anchor_longitude'] = list(rs_user_anchor_longitude)

        #             rs_by_state = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=rs_update.administrative_area_level_1).values('administrative_area_level_1').annotate(anchor_count=Count('id'))
                
        #             if rs_by_state:
        #                 j = 0
        #                 update_set_array[i]['states'] = list(rs_by_state)
        #                 for s in rs_by_state:
        #                     rs_state_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values_list('id', flat=True)

        #                     rs_state_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values_list('latitude', flat=True)

        #                     rs_state_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values_list('longitude', flat=True)   

        #                     rs_by_city = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=rs_update.location).values('location').annotate(anchor_count=Count('id'))
        #                     update_set_array[i]['states'][j]['parent_id'] = 2
        #                     update_set_array[i]['states'][j]['user_anchor_ids'] = list(rs_state_user_anchor_ids)
        #                     update_set_array[i]['states'][j]['user_anchor_latitude'] = list(rs_state_user_anchor_latitude)
        #                     update_set_array[i]['states'][j]['user_anchor_longitude'] = list(rs_state_user_anchor_longitude)
        #                     update_set_array[i]['states'][j]['cities'] = list(rs_by_city)
                            
        #                     if rs_by_city:
        #                         k = 0
        #                         for ct in rs_by_city:
        #                             rs_city_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('id', flat=True)

        #                             rs_city_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('latitude', flat=True)

        #                             rs_city_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('longitude', flat=True)

        #                             update_set_array[i]['states'][j]['cities'][k]['user_anchor_ids'] = list(rs_city_user_anchor_ids)
        #                             update_set_array[i]['states'][j]['cities'][k]['user_anchor_latitude'] = list(rs_city_user_anchor_latitude)
        #                             update_set_array[i]['states'][j]['cities'][k]['user_anchor_longitude'] = list(rs_city_user_anchor_longitude)
        #                             k = k+1
        #                     j = j+1
        #             i = i+1
        ##### End: Create Update Array Set For GroupWiseAncherLocationLabel #####



        ##### Start: Create Delet Array Set For GroupWiseAncherLocationLabel #####
        rs_by_record = UserAnchor.objects.filter(id=203).first()
        deleted_country = rs_by_record.country
        deleted_state = rs_by_record.administrative_area_level_1
        deleted_city = rs_by_record.location

        rs_by_country = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=rs_by_record.country).values('country').annotate(anchor_count=Count('id'))
        
        ##### Start: Create Decrise Array Set For GroupWiseAncherLocationLabel #####
        i = 0
        set_array = []
        if rs_by_country:
            for c in rs_by_country:
                rs_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('id', flat=True)

                rs_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('latitude', flat=True)

                rs_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country']).values_list('longitude', flat=True)

                set_array.append(c)
                set_array[i]['parent_id'] = 1
                set_array[i]['user_anchor_ids'] = list(rs_user_anchor_ids)
                set_array[i]['user_anchor_latitude'] = list(rs_user_anchor_latitude)
                set_array[i]['user_anchor_longitude'] = list(rs_user_anchor_longitude)

                rs_by_state = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=rs_by_record.administrative_area_level_1).values('administrative_area_level_1').annotate(anchor_count=Count('id'))
                
                if rs_by_state:
                    j = 0
                    set_array[i]['states'] = list(rs_by_state)
                    for s in rs_by_state:
                        rs_state_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values_list('id', flat=True)

                        rs_state_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values_list('latitude', flat=True)

                        rs_state_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1']).values_list('longitude', flat=True)   

                        rs_by_city = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=rs_by_record.location).values('location').annotate(anchor_count=Count('id'))
                        set_array[i]['states'][j]['parent_id'] = 2
                        set_array[i]['states'][j]['user_anchor_ids'] = list(rs_state_user_anchor_ids)
                        set_array[i]['states'][j]['user_anchor_latitude'] = list(rs_state_user_anchor_latitude)
                        set_array[i]['states'][j]['user_anchor_longitude'] = list(rs_state_user_anchor_longitude)
                        
                        if rs_by_city:
                            k = 0
                            set_array[i]['states'][j]['cities'] = list(rs_by_city)
                            for ct in rs_by_city:
                                rs_city_user_anchor_ids = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('id', flat=True)

                                rs_city_user_anchor_latitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('latitude', flat=True)

                                rs_city_user_anchor_longitude = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, country=c['country'], administrative_area_level_1=s['administrative_area_level_1'], location=ct['location']).values_list('longitude', flat=True)

                                set_array[i]['states'][j]['cities'][k]['parent_id'] = 2
                                set_array[i]['states'][j]['cities'][k]['user_anchor_ids'] = list(rs_city_user_anchor_ids)
                                set_array[i]['states'][j]['cities'][k]['user_anchor_latitude'] = list(rs_city_user_anchor_latitude)
                                set_array[i]['states'][j]['cities'][k]['user_anchor_longitude'] = list(rs_city_user_anchor_longitude)
                                k = k+1
                        else:
                            default_city_array = [{
                                "location": deleted_city,
                                "anchor_count": 0,
                                "parent_id": 2,
                                "user_anchor_ids": [],
                                "user_anchor_latitude": [],
                                "user_anchor_longitude": []
                            }]
                            set_array[i]['states'][j]['cities'] = default_city_array
                        j = j+1
                else:
                    default_state_array = [{
                    "administrative_area_level_1": deleted_state,
                    "anchor_count": 0,
                    "parent_id": 2,
                    "user_anchor_ids": [],
                    "user_anchor_latitude": [],
                    "user_anchor_longitude": [],
                    "cities": [{
                            "location": deleted_city,
                            "anchor_count": 0,
                            "parent_id": 2,
                            "user_anchor_ids": [],
                            "user_anchor_latitude": [],
                            "user_anchor_longitude": []
                        }]
                }]
                    set_array[i]['states'] = default_state_array
                i = i+1
        else:
            #### Create Blank Obj Set #####
            set_array.append({
            "country": deleted_country,
            "anchor_count": 0,
            "parent_id": 1,
            "user_anchor_ids": [],
            "user_anchor_latitude": [],
            "user_anchor_longitude": [],
            "states": [{
                    "administrative_area_level_1": deleted_state,
                    "anchor_count": 0,
                    "parent_id": 2,
                    "user_anchor_ids": [],
                    "user_anchor_latitude": [],
                    "user_anchor_longitude": [],
                    "cities": [{
                            "location": deleted_city,
                            "anchor_count": 0,
                            "parent_id": 2,
                            "user_anchor_ids": [],
                            "user_anchor_latitude": [],
                            "user_anchor_longitude": []
                        }]
                }]
        })
        #### Create Blank Obj Set #####

        ###### Update the Deleted Record ###########
        if len(set_array) > 0:
            for c in set_array:
                country_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, state__isnull=True, city__isnull=True, country=c['country']).update(user_anchor_ids= c['user_anchor_ids'], user_anchor_latitudes= c['user_anchor_latitude'], user_anchor_longitude= c['user_anchor_longitude'], regiser_anchor_count=c['anchor_count'])

                if len(c['states']) > 0:
                    for s in c['states']:
                        state_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city__isnull=True, state=s['administrative_area_level_1'], country=c['country']).update(user_anchor_ids= s['user_anchor_ids'], user_anchor_latitudes= s['user_anchor_latitude'], user_anchor_longitude= s['user_anchor_longitude'], regiser_anchor_count=s['anchor_count'])

                        if len(s['cities']) > 0:
                            for ct in s['cities']:
                                city_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city=ct['location'], state=s['administrative_area_level_1'], country=c['country']).update(user_anchor_ids= ct['user_anchor_ids'], user_anchor_latitudes= ct['user_anchor_latitude'], user_anchor_longitude= ct['user_anchor_longitude'], regiser_anchor_count=ct['anchor_count'])

        ###### Update the Deleted Record ###########

        ##### Start: Create Delet Array Set For GroupWiseAncherLocationLabel #####

        # if len(set_array) > 0:
        #     for c in set_array:
        #         print('************ Country *************', c)
        #         country_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, state__isnull=True, city__isnull=True, country=c['country']).count()
        #         # print('&&&&&&&&&&&&&&&&7 country_rs 7&&&&&&&&&&&&&&&&&', country_rs)
        #         country_parent_id = 0
        #         if country_rs == 0:
        #             central_lat = float(0.00)
        #             central_lng = float(0.00)
        #             print('&&&&&&&&&&&&&&&&7 INSERT RECORD 7&&&&&&&&&&&&&&&&&')
        #             url = "https://nominatim.openstreetmap.org/?addressdetails=1&q=" + c['country'] +"&format=json&limit=1"
        #             response = requests.get(url)
        #             if response.status_code == 200:
        #                 json_result = response.json()
        #                 # print(json_result)
        #                 central_lat = float(json_result[0]["lat"])
        #                 central_lng = float(json_result[0]["lon"])
        #             obj = GroupWiseAncherLocationLabel.objects.create(
        #                 parent_id = 0,
        #                 label_type = 'country',
        #                 user_anchor_ids= c['user_anchor_ids'],
        #                 user_anchor_latitudes= c['user_anchor_latitude'],
        #                 user_anchor_longitude= c['user_anchor_longitude'],
        #                 center_latitude= central_lat,
        #                 center_longitude= central_lng,
        #                 country= c['country'],
        #                 regiser_anchor_count=c['anchor_count'],
        #                 created_date=timezone.now(),
        #                 modified_date=timezone.now(),
        #             )
        #             c['parent_id'] = obj.id
        #             country_parent_id = obj.id
        #         else:
        #             # print('&&&&&&&&&&&&&&&&7 UPDATE RECORD 7&&&&&&&&&&&&&&&&&')
        #             country_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, state__isnull=True, city__isnull=True, country=c['country']).update(user_anchor_ids= c['user_anchor_ids'], user_anchor_latitudes= c['user_anchor_latitude'], user_anchor_longitude= c['user_anchor_longitude'], regiser_anchor_count=c['anchor_count'])

        #             rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, state__isnull=True, city__isnull=True, country=c['country']).first()
        #             country_parent_id = rs.id
        #         if len(c['states']) > 0:
        #             for s in c['states']:
        #                 state_parent_id = 0
        #                 # print('************ State *************', s)
        #                 s['parent_id'] = country_parent_id
        #                 # print('************ State parent_id *************', s['parent_id'])
        #                 state_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city__isnull=True, country=c['country'], state=s['administrative_area_level_1']).count()
        #                 if state_rs == 0:
        #                     print('&&&&&&&&&&&&&&&&7 INSERT State RECORD 7&&&&&&&&&&&&&&&&&')
        #                     state_central_lat = float(0.00)
        #                     state_central_lng = float(0.00)
        #                     print('&&&&&&&&&&&&&&&&7 INSERT RECORD 7&&&&&&&&&&&&&&&&&')
        #                     url = "https://nominatim.openstreetmap.org/?addressdetails=1&q=" + s['administrative_area_level_1'] + "+" + c['country'] + "&format=json&limit=1"
        #                     response = requests.get(url)
        #                     if response.status_code == 200:
        #                         json_result = response.json()
        #                         print('State Json', json_result)
        #                         state_central_lat = float(json_result[0]["lat"])
        #                         state_central_lng = float(json_result[0]["lon"])

        #                     stateobj = GroupWiseAncherLocationLabel.objects.create(
        #                         parent_id = s['parent_id'],
        #                         label_type = 'state',
        #                         user_anchor_ids= s['user_anchor_ids'],
        #                         user_anchor_latitudes= s['user_anchor_latitude'],
        #                         user_anchor_longitude= s['user_anchor_longitude'],
        #                         center_latitude= state_central_lat,
        #                         center_longitude= state_central_lng,
        #                         country= c['country'],
        #                         state=s['administrative_area_level_1'],
        #                         regiser_anchor_count=s['anchor_count'],
        #                         created_date=timezone.now(),
        #                         modified_date=timezone.now(),
        #                     )
        #                     s['parent_id'] = stateobj.id
        #                     country_parent_id = stateobj.id
        #                 else:
        #                     print('&&&&&&&&&&&&&&&&7 Update State RECORD 7&&&&&&&&&&&&&&&&&')
        #                     state_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city__isnull=True, state=s['administrative_area_level_1'], country=c['country']).update(user_anchor_ids= s['user_anchor_ids'], user_anchor_latitudes= s['user_anchor_latitude'], user_anchor_longitude= s['user_anchor_longitude'], regiser_anchor_count=s['anchor_count'])

        #                     qs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city__isnull=True, state=s['administrative_area_level_1'], country=c['country']).first()
        #                     state_parent_id = qs.id

        #                 if len(s['cities']) > 0:
        #                     for ct in s['cities']:
        #                         print('************ City *************', ct)
        #                         ct['parent_id'] = state_parent_id
        #                         print('************ City  state_parent_id*************', ct['parent_id'])
        #                         city_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city=ct['location'], country=c['country'], state=s['administrative_area_level_1']).count()
        #                         city_parent_id = 0
        #                         if city_rs == 0:
        #                             print('&&&&&&&&&&&&&&&&7 INSERT CITY RECORD 7&&&&&&&&&&&&&&&&&')
        #                             city_central_lat = float(0.00)
        #                             city_central_lng = float(0.00)
        #                             print('&&&&&&&&&&&&&&&&7 INSERT RECORD 7&&&&&&&&&&&&&&&&&')
        #                             url = "https://nominatim.openstreetmap.org/?addressdetails=1&q=" + ct['location'] + "+" + s['administrative_area_level_1'] + "+" + c['country'] + "&format=json&limit=1"
        #                             response = requests.get(url)
        #                             if response.status_code == 200:
        #                                 json_result = response.json()
        #                                 print('State Json', json_result)
        #                                 city_central_lat = float(json_result[0]["lat"])
        #                                 city_central_lng = float(json_result[0]["lon"])

        #                             cityobj = GroupWiseAncherLocationLabel.objects.create(
        #                                 parent_id = ct['parent_id'],
        #                                 label_type = 'city',
        #                                 user_anchor_ids= ct['user_anchor_ids'],
        #                                 user_anchor_latitudes= ct['user_anchor_latitude'],
        #                                 user_anchor_longitude= ct['user_anchor_longitude'],
        #                                 center_latitude= city_central_lat,
        #                                 center_longitude= city_central_lng,
        #                                 country= c['country'],
        #                                 state=s['administrative_area_level_1'],
        #                                 city=ct['location'],
        #                                 regiser_anchor_count=ct['anchor_count'],
        #                                 created_date=timezone.now(),
        #                                 modified_date=timezone.now(),
        #                             )
        #                             ct['parent_id'] = cityobj.id
        #                             city_parent_id = cityobj.id
        #                         else:
        #                             print('&&&&&&&&&&&&&&&&7 Update City RECORD 7&&&&&&&&&&&&&&&&&')
        #                             city_rs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city=ct['location'], state=s['administrative_area_level_1'], country=c['country']).update(user_anchor_ids= ct['user_anchor_ids'], user_anchor_latitudes= ct['user_anchor_latitude'], user_anchor_longitude= ct['user_anchor_longitude'], regiser_anchor_count=ct['anchor_count'])

        #                             cqs = GroupWiseAncherLocationLabel.objects.filter(is_blocked=False, is_deleted=False, city=ct['location'], state=s['administrative_area_level_1'], country=c['country']).first()
        #                             ct['parent_id'] = cqs.id
        #                             city_parent_id = cqs.id

        response_data['status'] = 0
        response_data['insert_sets'] = set_array
        # response_data['update_sets'] = update_set_array
        # response_data['country'] = list(rs_by_country)
        # response_data['state'] = bset
        # response_data['city'] = list(rs_by_location)
        # response_data['city'] = list(rs_details)
        response_data['message'] = 'Request save failure.'
        return JsonResponse(response_data, status=200)

    # def put(self,request):
    #     user = request.user
    #     user_id = user.id
    #     response_data = {}
    #     requestData = request.data
    #     print('*****************  requestData  ******************', requestData)
    #     print(requestData)
    #     userAnchorObj = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, id=requestData['user_anchor_id']).first()
    #     if userAnchorObj:
    #         # obj = UserAnchor.objects.filter(id=requestData['user_anchor_id']).update(location=requestData['location'], latitude=requestData['latitude'], longitude=requestData['longitude'], address=requestData['address'], location_register_status='processing', modified_date=timezone.now())
    #         obj = UserAnchor.objects.filter(id=requestData['user_anchor_id']).update(latitude=requestData['latitude'], longitude=requestData['longitude'], location=requestData['location'], address=requestData['address'], location_register_status='processing', modified_date=timezone.now())
    #         # AnchorQrCode.objects.filter(id=userAnchorObj.anchor_qr_code_id).update(complete_regis='yes')
    #         response_data['status'] = 1
    #         response_data['message'] = 'User anchor update successfully.'
    #         return JsonResponse(response_data, status=200)
    #     else:
    #         response_data['status'] = 0
    #         response_data['message'] = 'Anchor not found.'
    #         return JsonResponse(response_data, status=200)


def create_parent_chield_node(data_set):
    a = data_set       
    # a = [(1, 1), (2, 1), (3, 1), (4, 3), (5, 3), (6, 3), (7, 7), (8, 7), (9, 7)]
    # pass 1: create nodes dictionary
    nodes = {}
    for i in a:
        # print(i)
        # id, parent_id = i
        id, parent_id, label_type, regiser_anchor_count, center_latitude, center_longitude, user_anchor_latitudes, user_anchor_longitude, user_anchor_ids, country, state, city, location = i
        nodes[id] = { 
            'id': id, 
            'parent_id': parent_id, 
            'label_type': label_type, 
            'regiser_anchor_count': str(regiser_anchor_count), 
            'center_latitude': float(center_latitude), 
            'center_longitude': float(center_longitude),
            'user_anchor_latitudes': user_anchor_latitudes,
            'user_anchor_longitude': user_anchor_longitude,
            'user_anchor_ids': user_anchor_ids,
            'country': country,
            'state': state, 
            'city': city, 
            'location': location
            }
        # nodes[id] = {'id': id, 'parent_id': parent_id, 'menu_name': menu_name}

    # pass 2: create trees and parent-child relations
    forest = []
    for i in a:
        id, parent_id, label_type, regiser_anchor_count, center_latitude, center_longitude, user_anchor_latitudes, user_anchor_longitude, user_anchor_ids, country, state, city, location = i
        node = nodes[id]
        node['children'] = []
        # either make the node a new tree or link it to its parent
        # if id == parent_id:
        #     # start a new tree in the forest
        #     forest.append(node)
        if parent_id == 0:
            # start a new tree in the forest
            forest.append(node)
        else:
            # add new_node as child to parent
            parent = nodes[parent_id]
            if not 'children' in parent:
                # ensure parent has a 'children' field
                parent['children'] = []
            children = parent['children']
            children.append(node)

    return forest

class AnchorMapCoordinatesView(APIView):
    # permission_classes = (IsAuthenticated,)
    def get(self,request):
        import requests
        import urllib.parse
        user = request.user
        user_id = user.id
        response_data = {}
        rs = GroupWiseAncherLocationLabel.objects.filter(is_deleted=False, is_blocked=False).exclude(regiser_anchor_count=0).values_list('id', 'parent_id', 'label_type', 'regiser_anchor_count', 'center_latitude', 'center_longitude', 'user_anchor_latitudes', 'user_anchor_longitude', 'user_anchor_ids', 'country', 'state', 'city', 'location').order_by('id')
        # print(rs)
        if rs:
            set_data = create_parent_chield_node(rs)
            # serializer = AnchorMapCoordinatesSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Anchor list.'
            # response_data['anchor'] = serializer.data
            response_data['map_coodinets'] = set_data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Anchor list blank.'
            response_data['anchor'] = []
            return JsonResponse(response_data, status=200)


class ActiveAnchorZoneCountView(APIView):
    #permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user

        # ✅ Filter active anchors
        if user.is_superuser:
            anchors = UserAnchor.objects.filter(
                is_deleted=False,
                is_blocked=False,
                status="active",
                anchor__is_online=True
            )
        else:
            anchors = UserAnchor.objects.filter(
                is_deleted=False,
                is_blocked=False,
                status="active",
                anchor__is_online=True
            ).exclude(user__is_superuser=True)

        if not anchors.exists():
            return JsonResponse({
                "status": 0,
                "message": "No active anchors found.",
                "zone_counts": {}
            }, status=200)

        # ✅ Initialize counters
        zone_counts = {
            "North": 0,
            "South": 0,
            "East": 0,
            "West": 0,
        }

        # ✅ Define Indian zone boundaries (approx)
        for anchor in anchors:
            try:
                lat = float(anchor.latitude)
                lon = float(anchor.longitude)

                # 🟢 North India — (Delhi, Punjab, Himachal, Uttarakhand, etc.)
                if 25 <= lat <= 37 and 73 <= lon <= 85:
                    zone_counts["North"] += 1
                # 🔵 South India — (Kerala, Tamil Nadu, Karnataka, AP)
                elif 8 <= lat <= 20 and 73 <= lon <= 85:
                    zone_counts["South"] += 1
                # 🟠 East India — (Odisha, WB, Bihar, Jharkhand)
                elif 20 <= lat <= 27 and 85 <= lon <= 97:
                    zone_counts["East"] += 1
                # 🟣 West India — (Gujarat, Maharashtra, Rajasthan)
                elif 15 <= lat <= 25 and 68 <= lon <= 80:
                    zone_counts["West"] += 1
                else:
                    # If coordinate is slightly outside the defined box, map to nearest zone
                    if lat > 25 and lon > 85:
                        zone_counts["East"] += 1
                    elif lat < 20 and lon < 80:
                        zone_counts["South"] += 1
                    elif lon < 75:
                        zone_counts["West"] += 1
                    else:
                        zone_counts["North"] += 1

            except (TypeError, ValueError):
                # if bad data, just skip
                continue

        return JsonResponse({
            "status": 1,
            "message": "Active anchors count by Indian zone.",
            "zone_counts": zone_counts,
            "total_active": sum(zone_counts.values())
        }, status=200)

class RegisteredAnchorZoneCountView(APIView):
    #permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user

        # ✅ Filter active anchors
        if user.is_superuser:
            anchors = UserAnchor.objects.filter(
                is_deleted=False,
                is_blocked=False,
                status="active",
                location_register_status='registered',

            )
        else:
            anchors = UserAnchor.objects.filter(
                is_deleted=False,
                is_blocked=False,
                status="active",
                location_register_status='registered',

            ).exclude(user__is_superuser=True)

        if not anchors.exists():
            return JsonResponse({
                "status": 0,
                "message": "No registered anchors found.",
                "zone_counts": {}
            }, status=200)

        # ✅ Initialize counters
        zone_counts = {
            "North": 0,
            "South": 0,
            "East": 0,
            "West": 0,
        }

        # ✅ Define Indian zone boundaries (approx)
        for anchor in anchors:
            try:
                lat = float(anchor.latitude)
                lon = float(anchor.longitude)

                # 🟢 North India — (Delhi, Punjab, Himachal, Uttarakhand, etc.)
                if 25 <= lat <= 37 and 73 <= lon <= 85:
                    zone_counts["North"] += 1
                # 🔵 South India — (Kerala, Tamil Nadu, Karnataka, AP)
                elif 8 <= lat <= 20 and 73 <= lon <= 85:
                    zone_counts["South"] += 1
                # 🟠 East India — (Odisha, WB, Bihar, Jharkhand)
                elif 20 <= lat <= 27 and 85 <= lon <= 97:
                    zone_counts["East"] += 1
                # 🟣 West India — (Gujarat, Maharashtra, Rajasthan)
                elif 15 <= lat <= 25 and 68 <= lon <= 80:
                    zone_counts["West"] += 1
                else:
                    # If coordinate is slightly outside the defined box, map to nearest zone
                    if lat > 25 and lon > 85:
                        zone_counts["East"] += 1
                    elif lat < 20 and lon < 80:
                        zone_counts["South"] += 1
                    elif lon < 75:
                        zone_counts["West"] += 1
                    else:
                        zone_counts["North"] += 1

            except (TypeError, ValueError):
                # if bad data, just skip
                continue

        return JsonResponse({
            "status": 1,
            "message": "Registered anchors count by Indian zone.",
            "zone_counts": zone_counts,
            "total_registered": sum(zone_counts.values())
        }, status=200)
