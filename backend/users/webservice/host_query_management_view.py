from rest_framework.response import Response

from django.http import JsonResponse
from backend.users.serializers import *
from backend.users.models import *
from backend.anchor.models import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class HostGroupView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        rs = UsersHostGroup.objects.filter(user_id=user_id, is_deleted=False).order_by('-id')
        if rs:
            serializer = UserHostGroupViewSerializer(rs, many=True)
            for hostgroup in serializer.data:
                ## Get Domain details from UsersHostGroupDomain table
                groupdomainObj = UsersHostGroupDomain.objects.filter(user_id=user_id,
                                                                     user_host_group_id=hostgroup['id'])
                if groupdomainObj:
                    for groupDomain in groupdomainObj:
                        domainObj = UsersDomain.objects.filter(user_id=user_id, id=groupDomain.domain_id,
                                                               is_deleted=False).first()
                        if domainObj:
                            hostgroup['domain_details'].append(
                                {"domain_id": domainObj.id, "domain_name": domainObj.domain_name,
                                 "domain_ip": domainObj.domain_ip})
            response_data['status'] = 1
            response_data['message'] = 'Host group list.'
            response_data['hostgroup'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Host group not found.'
            response_data['hostgroup'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        print(requestData)
        try:
            if user:
                if len(requestData['domain_ids']) > 0:
                    HostGroupObj = UsersHostGroup.objects.create(
                        user_id=user_id,
                        host_group_name=requestData['host_group_name'],
                        created_date=timezone.now(),
                        modified_date=timezone.now(),
                    )
                    if HostGroupObj:
                        for domain_id in requestData['domain_ids']:
                            HostGroupDomainObj = UsersHostGroupDomain.objects.create(
                                user_id=user_id,
                                user_host_group_id=HostGroupObj.id,
                                domain_id=int(domain_id),
                                created_date=timezone.now(),
                                modified_date=timezone.now(),
                            )
                        response_data['status'] = 1
                        response_data['message'] = 'Host group save successfully.'
                        return JsonResponse(response_data, status=200)
                    else:
                        response_data['status'] = 0
                        response_data['message'] = 'Host group not create.'
                        return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Domain ids format is array and its required field.'
                    return JsonResponse(response_data, status=401)
            else:
                response_data['status'] = 0
                response_data['message'] = 'User not found.'
                return JsonResponse(response_data, status=401)
        except:
            response_data['status'] = 0
            response_data['message'] = 'Something want wrong.'
            return JsonResponse(response_data, status=404)

    def put(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        is_delete = request.data.get('is_delete', None)
        requestData = request.data
        rs = UsersHostGroup.objects.filter(user_id=user_id, id=requestData['id'])
        if rs:
            if is_delete is not None:
                UsersHostGroup.objects.filter(id=requestData['id']).update(is_deleted=is_delete,
                                                                           modified_date=timezone.now())
                response_data['status'] = 1
                response_data['message'] = 'Host group delete successfully.'
                return JsonResponse(response_data, status=200)
            else:
                if len(requestData['domain_ids']) > 0:
                    ## Delete first objects from UsersHostGroupDomain table
                    deletObj = UsersHostGroupDomain.objects.filter(user_id=user_id,
                                                                   user_host_group_id=requestData['id']).delete()
                    if deletObj:
                        UsersHostGroup.objects.filter(id=requestData['id']).update(
                            host_group_name=requestData['host_group_name'], modified_date=timezone.now())
                        ## New insert into UsersHostGroupDomain table
                        for domain_id in requestData['domain_ids']:
                            HostGroupDomainObj = UsersHostGroupDomain.objects.create(
                                user_id=user_id,
                                user_host_group_id=requestData['id'],
                                domain_id=int(domain_id),
                                created_date=timezone.now(),
                                modified_date=timezone.now(),
                            )
                    response_data['status'] = 1
                    response_data['message'] = 'Host group update successfully.'
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Domain ids format is array and its required field.'
                    return JsonResponse(response_data, status=401)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Host group not found.'
            return JsonResponse(response_data, status=200)


class HostGroupDetailsView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        rs = UsersHostGroup.objects.filter(user_id=user_id, is_deleted=False, id=requestData['host_group_id'])
        if rs:
            serializer = UserHostGroupViewSerializer(rs, many=True)
            for hostgroup in serializer.data:
                ## Get Domain details from UsersHostGroupDomain table
                groupdomainObj = UsersHostGroupDomain.objects.filter(user_id=user_id,
                                                                     user_host_group_id=hostgroup['id'])
                if groupdomainObj:
                    for groupDomain in groupdomainObj:
                        domainObj = UsersDomain.objects.filter(user_id=user_id, id=groupDomain.domain_id,
                                                               is_deleted=False).first()
                        if domainObj:
                            hostgroup['domain_details'].append(
                                {"domain_id": domainObj.id, "domain_name": domainObj.domain_name,
                                 "domain_ip": domainObj.domain_ip})
            response_data['status'] = 1
            response_data['message'] = 'Host group details'
            response_data['hostgroup'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This host group is not present in our database'
            response_data['hostgroup'] = []
            return JsonResponse(response_data, status=200)


class ZoneView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        rs = UsersZone.objects.filter(user_id=user_id, is_deleted=False).order_by('-id')
        if rs:
            serializer = UsersZoneViewSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Zone list.'
            response_data['zone'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Zone not found.'
            response_data['zone'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        print(requestData)
        # try:
        if user:
            if len(requestData['user_anchor_ids']) > 0:
                print('*************')
                userAnchorObj = UserAnchor.objects.filter(id__in=requestData['user_anchor_ids']).values('latitude',
                                                                                                        'longitude',
                                                                                                        'location',
                                                                                                        'anchor_id__anchor_name').order_by(
                    'id')
                latitudes = []
                longitudes = []
                locations = []
                anchor_names = []
                if userAnchorObj:
                    for n in userAnchorObj:
                        latitudes.append(n['latitude'])
                        longitudes.append(n['longitude'])
                        locations.append(n['location'])
                        anchor_names.append(n['anchor_id__anchor_name'])
                        user_anchor_ids = requestData['user_anchor_ids']
                    print('****** latitudes *******', latitudes)
                    print('****** longitudes *******', longitudes)
                    print('****** locations *******', locations)
                    print('****** anchor_names *******', anchor_names)
                    print('****** user_anchor_ids *******', user_anchor_ids)

                    UsersZoneObj = UsersZone.objects.create(
                        user_id=user_id,
                        user_zone_name=requestData['zone_name'],
                        user_anchor_ids=user_anchor_ids,
                        user_anchor_names=anchor_names,
                        user_anchor_latitudes=latitudes,
                        user_anchor_longitudes=longitudes,
                        user_anchor_locations=locations,
                        created_date=timezone.now(),
                        modified_date=timezone.now(),
                    )
                    response_data['status'] = 1
                    response_data['anchors'] = list(userAnchorObj)
                    response_data['message'] = 'Zone save successfully.'
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Zone not create because anchors not found.'
                    return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'Zone user anchor ids is array and its required field.'
                return JsonResponse(response_data, status=401)
        else:
            response_data['status'] = 0
            response_data['message'] = 'User not found.'
            return JsonResponse(response_data, status=401)
        # except:
        #     response_data['status'] = 0
        #     response_data['message'] = 'Something want wrong.'
        #     return JsonResponse(response_data, status=404)

    def put(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        is_delete = request.data.get('is_delete', None)
        requestData = request.data
        rs = UsersZone.objects.filter(user_id=user_id, id=requestData['zone_id'])
        if rs:
            if is_delete is not None:
                UsersZone.objects.filter(id=requestData['zone_id']).update(is_deleted=is_delete,
                                                                           modified_date=timezone.now())
                response_data['status'] = 1
                response_data['message'] = 'Zone delete successfully.'
                return JsonResponse(response_data, status=200)
            else:
                if len(requestData['zone_area']) > 0:
                    ## Delete first objects from UsersHostGroupDomain table
                    deletObj = UsersZoneAreaDetails.objects.filter(user_id=user_id,
                                                                   user_zone_id=requestData['zone_id']).delete()
                    if deletObj:
                        UsersZone.objects.filter(id=requestData['zone_id']).update(
                            user_zone_name=requestData['zone_name'], user_zone_country_name=requestData['zone_country'],
                            user_zone_state_name=requestData['zone_state'], modified_date=timezone.now())
                        ## New insert into UsersHostGroupDomain table
                        for area in requestData['zone_area']:
                            ZoneAreaObj = UsersZoneAreaDetails.objects.create(
                                user_id=user_id,
                                user_zone_id=requestData['zone_id'],
                                area_name=str(area),
                                created_date=timezone.now(),
                                modified_date=timezone.now(),
                            )
                    response_data['status'] = 1
                    response_data['message'] = 'Zone update successfully.'
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Zone area format is array and its required field.'
                    return JsonResponse(response_data, status=401)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Zone not found.'
            return JsonResponse(response_data, status=200)


class ZoneDetailsView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        rs = UsersZone.objects.filter(user_id=user_id, is_deleted=False, id=requestData['zone_id']).first()
        if rs:
            serializer = UsersZoneViewSerializer(rs)
            response_data['status'] = 1
            response_data['message'] = 'Zone details'
            response_data['zone'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This zone is not present in our database'
            response_data['zone'] = []
            return JsonResponse(response_data, status=200)


class UserReportZoneView(APIView):
    def post(self, request):
        requestData = request.data
        user = request.user
        user_email = user.email
        response_data = {}
        admin_status = User.objects.filter(email=user_email, is_active=True, is_blocked=False, is_deleted=False).first()
        if admin_status.is_superuser:
            get_zone_details = UsersZone.objects.filter(user_id=requestData['user_id'], is_blocked=False,
                                                        is_deleted=False)
            if get_zone_details:
                serializer = UsersZoneViewSerializer(get_zone_details, many=True)
                response_data['status'] = 1
                response_data['msg'] = "User Zone details"
                response_data['User_zone_details'] = serializer.data
                http_status_code = 200
            else:
                response_data['status'] = 0
                response_data['msg'] = 'No Zone Deatils'
                response_data['User_zone_details'] = []
                http_status_code = 404
        else:
            response_data['status'] = 0
            response_data['msg'] = 'you are not admin'
            response_data['User_zone_details'] = []
            http_status_code = 404
        return Response(response_data, status=http_status_code)


class UserReportHostGroupView(APIView):
    def post(self, request):
        requestData = request.data
        user = request.user
        user_email = user.email
        response_data = {}
        admin_status = User.objects.filter(email=user_email, is_active=True, is_blocked=False, is_deleted=False).first()
        if admin_status.is_superuser:
            get_host_group_details = UsersHostGroup.objects.filter(user_id=requestData['user_id'], is_blocked=False,
                                                                   is_deleted=False)
            if get_host_group_details:
                serializer = UserHostGroupViewSerializer(get_host_group_details, many=True)
                for hostgroup in serializer.data:
                    ## Get Domain details from UsersHostGroupDomain table
                    groupdomainObj = UsersHostGroupDomain.objects.filter(user_id=requestData['user_id'],
                                                                         user_host_group_id=hostgroup['id'])
                    if groupdomainObj:
                        for groupDomain in groupdomainObj:
                            domainObj = UsersDomain.objects.filter(user_id=requestData['user_id'],
                                                                   id=groupDomain.domain_id, is_deleted=False).first()
                            if domainObj:
                                hostgroup['domain_details'].append(
                                    {"domain_id": domainObj.id, "domain_name": domainObj.domain_name,
                                     "domain_ip": domainObj.domain_ip})
                response_data['status'] = 1
                response_data['msg'] = "User Host Group details"
                response_data['User_host_group_details'] = serializer.data
                http_status_code = 200
            else:
                response_data['status'] = 0
                response_data['msg'] = 'No Deatils'
                response_data['User_host_group_details'] = []
                http_status_code = 404
        else:
            response_data['status'] = 0
            response_data['msg'] = 'you are not admin'
            response_data['User_host_group_details'] = []
            http_status_code = 404
        return Response(response_data, status=http_status_code)
