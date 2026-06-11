from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sessions.models import Session
from django.utils.crypto import get_random_string
from django.conf import settings
from rest_framework import generics, permissions, status, views, mixins
from rest_framework.pagination import PageNumberPagination
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
from django.db.models import F, Max, Count, Sum, Avg
from django.db.models import F, Q
from backend.anchor.models import *
from backend.users.models import *
from backend.anchor.serializers import *
from backend.users.serializers import *
import json
from django.utils import timezone
import requests


def checkKey(dict, key):
    if key in dict:
        print("Present")
        # print("value =", dict[key])
        return 1
    else:
        print("Not present")
        return 0


class CommandHistoryView(APIView):
    permission_classes = (IsAuthenticated,)

    # def get(self,request):
    #     user = request.user
    #     user_id = user.id
    #     response_data = {}
    #     rs=CommendExecutionHistory.objects.filter(user_id=user_id, is_deleted=False, check_points_status='success').order_by('-id')
    #     if rs:
    #         serializer = QueryReportsSerializer(rs, many=True)
    #
    #         response_data['status'] = 1
    #         response_data['message'] = 'History list.'
    #         response_data['history'] = serializer.data
    #         return JsonResponse(response_data, status=200)
    #     else:
    #         response_data['status'] = 1
    #         response_data['message'] = 'History list blank.'
    #         response_data['history'] = []
    #         return JsonResponse(response_data, status=200)

    # def get(self, request):
    #     user_id = request.user.id
    #     response_data = {}
    #
    #     # Base filters always applied
    #     filters = {
    #         'user_id': user_id,
    #         'is_deleted': False,
    #         'check_points_status': 'success'
    #     }
    #
    #     # If is_public param is present, add it to filters (no filtering otherwise)
    #     is_public_param = request.GET.get('is_public', None)
    #     if is_public_param is not None:
    #         val = is_public_param.strip().lower()
    #         if val in ('1', 'true', 'yes'):
    #             filters['is_public'] = True
    #         elif val in ('0', 'false', 'no'):
    #             filters['is_public'] = False
    #         # if param is present but not parseable, ignore it (no is_public filter)
    #
    #     qs = CommendExecutionHistory.objects.filter(**filters).order_by('-id')
    #     serializer = QueryReportsSerializer(qs, many=True)
    #
    #     response_data['status'] = 1
    #     response_data['message'] = 'History list.' if serializer.data else 'History list blank.'
    #     response_data['history'] = serializer.data
    #
    #     return JsonResponse(response_data, status=200)
    def get(self, request):
        user_id = request.user.id

        # Base filters
        filters = {
            'user_id': user_id,
            'is_deleted': False,
            'check_points_status': 'success'
        }

        # Optional filter for is_public
        is_public_param = request.GET.get('is_public')
        if is_public_param is not None:
            val = is_public_param.strip().lower()
            if val in ('1', 'true', 'yes'):
                filters['is_public'] = True
            elif val in ('0', 'false', 'no'):
                filters['is_public'] = False

        qs = CommendExecutionHistory.objects.filter(**filters)

        # --- Query search ---
        query_param = request.GET.get('query')
        if query_param:
            terms = [t.strip() for t in query_param.split(',') if t.strip()]
            q_filter = Q()
            for term in terms:
                q_filter |= Q(query=term) | Q(query__icontains=term)
            qs = qs.filter(q_filter)

        # --- Query type search ---
        query_type_param = request.GET.get('query_type')
        if query_type_param:
            types = [t.strip() for t in query_type_param.split(',') if t.strip()]
            qs = qs.filter(query_type__in=types)

        qs = qs.order_by('-id')

        # Pagination
        paginator = CustomPageNumberPagination()
        paginated_qs = paginator.paginate_queryset(qs, request)
        serializer = QueryReportsSerializer(paginated_qs, many=True)

        # Build response
        response_data = {
            'status': 1,
            'message': 'History list.' if serializer.data else 'History list blank.',
            'pagination': {
                'count': paginator.page.paginator.count,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'page_size': paginator.get_page_size(request),
            },
            'history': serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = dict(request.data)
        # print('############## Insert Execution Record ###############', requestData)
        # print('############## Insert Execution Record ###############', requestData['cmd_value'])
        host_ids = []
        host_name = ''
        hosts = requestData['hosts']
        anchor_ids = []
        anchor_names = ''
        region = requestData['region']
        query = requestData['cmd_value']
        query_type = requestData['cmd_type']
        ## Get Domain Details
        domainqs = UsersDomain.objects.filter(domain_ip=requestData['hosts']).first()
        if domainqs:
            host_ids.append(domainqs.id)
            host_name = domainqs.domain_name

        ## Get Anchor Details
        userAnchorRS = UserAnchor.objects.filter(id=requestData['anchor_ids']).first()
        if userAnchorRS:
            # print('Anchor Ids RESULT', n.anchor_id)
            anchorRS = Anchor.objects.filter(id=userAnchorRS.anchor_id).first()
            if anchorRS:
                anchor_ids.append(anchorRS.id)
                anchor_names = anchorRS.anchor_name
        print('############## Insert Execution Host Id ###############', host_ids)
        # print('############## Insert Execution Host Name ###############', host_name)
        # print('############## Insert Execution Host ###############', hosts)
        # print('############## Insert Execution Anchor Id ###############', anchor_ids)
        # print('############## Insert Execution Anchor Name ###############', anchor_names)
        # print('############## Insert Execution region ###############', region)
        # response_data['status'] = 1
        # response_data['obj_id'] = 135
        # response_data['message'] = 'History save successfully.'
        # return JsonResponse(response_data, status=200)
        if requestData:
            obj = CommendExecutionHistory.objects.create(
                user_id=user_id,
                commend_query_id='',
                commend_request_payload=requestData,
                host_ids=host_ids,
                host_name=host_name,
                hosts=hosts,
                anchor_ids=anchor_ids,
                anchor_names=anchor_names,
                region=region,
                query=query,
                query_type=query_type,
                created_date=timezone.now(),
                modified_date=timezone.now(),
                query_execution_end_date=timezone.now(),
            )
            response_data['status'] = 1
            response_data['obj_id'] = obj.id
            response_data['message'] = 'History save successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'History save failure.'
            return JsonResponse(response_data, status=200)

    def put(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        is_view = request.data.get('is_view', None)
        requestData = request.data

        rs = CommendExecutionHistory.objects.filter(id=requestData['id'])
        if rs:
            if is_view is not None:
                CommendExecutionHistory.objects.filter(id=requestData['id']).update(has_been_seen=True)
            else:
                CommendExecutionHistory.objects.filter(id=requestData['id']).update(
                    commend_query_id=requestData['query_id'], server_hit_status=requestData['status'],
                    query_status=requestData['status'])
            response_data['status'] = 1
            response_data['message'] = 'History update successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'History update failure.'
            return JsonResponse(response_data, status=200)

    def patch(self, request):
        user = request.user
        request_data = request.data
        record_id = request_data.get('id')

        if not record_id:
            return JsonResponse({"status": 0, "message": "ID is required."}, status=400)

        try:
            record = CommendExecutionHistory.objects.get(id=record_id)
        except CommendExecutionHistory.DoesNotExist:
            return JsonResponse({"status": 0, "message": "Record not found."}, status=404)

        # Only update fields that exist in the model
        valid_fields = {field.name for field in CommendExecutionHistory._meta.fields}
        update_data = {k: v for k, v in request_data.items() if k in valid_fields and k != 'id'}

        if update_data:
            update_data['modified_date'] = timezone.now()  # optional if you track updates
            CommendExecutionHistory.objects.filter(id=record_id).update(**update_data)

        return JsonResponse({
            "status": 1,
            "message": "History updated successfully.",
            "updated_fields": update_data
        }, status=200)

# Added on 09-08-2025
class CustomPageNumberPagination(PageNumberPagination):
    page_size = 15  # default
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommendExecutionHistoryListAPIView(generics.ListAPIView):
    serializer_class = QueryReportsSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = CommendExecutionHistory.objects.all().order_by('-created_date')

        # Filtering parameters
        is_public = self.request.query_params.get('is_public')
        query_type = self.request.query_params.get('query_type')
        query_status = self.request.query_params.get('query_status')

        if is_public is not None:
            if is_public.lower() == "true":
                queryset = queryset.filter(is_public=True)
            elif is_public.lower() == "false":
                queryset = queryset.filter(is_public=False)

        if query_type:
            queryset = queryset.filter(query_type=query_type)

        if query_status:
            queryset = queryset.filter(query_status=query_status)

        return queryset


class PeriodicCommandHistoryWithZoneOrAnchorView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        response_data = {}

        token, created = Token.objects.get_or_create(user=user)  ### Get user authentication token
        token_data = token.key  ### if it is first login then create token first and get token
        # rs=CommendExecutionHistory.objects.filter(user_id=user_id, is_deleted=False).order_by('-id')
        # if rs:
        #     serializer = CommandHitRequestHistorySerializer(rs, many=True)
        #     response_data['status'] = 1
        #     response_data['message'] = 'History list.'
        #     response_data['history'] = serializer.data
        #     return JsonResponse(response_data, status=200)
        # else:
        #     response_data['status'] = 1
        #     response_data['message'] = 'History list blank.'
        #     response_data['history'] = []
        #     return JsonResponse(response_data, status=200)
        response_data['status'] = 1
        response_data['message'] = 'History list.'
        response_data['query_id'] = get_random_string(length=50)
        return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = dict(request.data)
        execution_end_date = timezone.now()
        execution_end_date = timezone.now()
        # print('############## Insert Execution Record ###############', requestData)
        # print('############## Insert Execution Record ###############', requestData['cmd_value'])

        host_ids = []
        host_name = ''
        hosts = ''
        anchor_ids = []
        region = ''
        anchor_names = ''
        zone_id = []
        zone_names = ''
        query = requestData['cmd_value']
        insert_array = []
        ## Get Domain Details
        if len(requestData['host_id']) > 0:
            domainQs = UsersDomain.objects.filter(domain_ip=requestData['host_id']).first()
            # domainQs = domainQs.values('id', 'domain_name', 'domain_ip')
            if domainQs:
                host_name += domainQs.domain_name
                hosts += domainQs.domain_ip
                host_ids.append(domainQs.id)

            print('############## Insert Execution Host Id ###############', host_ids)
            # print('############## Insert Execution Host Name ###############', host_name)
            # print('############## Insert Execution Hosts ###############', hosts)
            # print('############## Insert Execution query ###############', query)
        # Get Anchor Details
        if len(requestData['anchor_id']) > 0:
            userAnchorRS = UserAnchor.objects.filter(id__in=requestData['anchor_id'])
            userAnchorRS = userAnchorRS.values('id', 'location', 'anchor_id__anchor_name', 'anchor_id__anchor_id',
                                               'anchor_id', 'lease_id', 'user_id')
            if userAnchorRS:
                for anchor in userAnchorRS:
                    anchor_names = anchor['anchor_id__anchor_name']
                    region = anchor['location']
                    anchor_ids.append(anchor['anchor_id'])
                    insert_array.append({
                        "cmd_value": requestData['cmd_value'],
                        "cmd_type": requestData['cmd_type'],
                        "region": region,
                        "user_anchor_id": anchor['id'],
                        "anchors": str(anchor['anchor_id__anchor_id']).split(),
                        "run_time": requestData['run_time'],
                        "time_unit": requestData['time_unit'],
                        "run_count": requestData['run_count'],
                        "interval_unit": requestData['interval_unit'],
                        "interval_time": requestData['interval_time'],
                        "hosts": str(hosts).split(),
                        "host_id": domainQs.id,
                        "host_name": domainQs.domain_name,
                        "host_ip": domainQs.domain_ip,
                        "zone_id": 0,
                        "zone_area_name": "",
                        "anchor_id": anchor['anchor_id'],
                        "host_group_id": '',
                        "lease_id": anchor['lease_id'],
                        "anchor_names": anchor_names,
                        "user_id": anchor['user_id']
                    })
        # Get Anchor Details From Zone
        if len(requestData['zone_id']) > 0:
            userZoneRS = UsersZone.objects.filter(id__in=requestData['zone_id'])
            if userZoneRS:
                for an in userZoneRS:
                    zone_names = an.user_zone_name
                    userAnchorRS = UserAnchor.objects.filter(id__in=an.user_anchor_ids)
                    userAnchorRS = userAnchorRS.values('id', 'location', 'anchor_id__anchor_name',
                                                       'anchor_id__anchor_id', 'anchor_id', 'lease_id', 'user_id')
                    if userAnchorRS:
                        i = 0
                        for n in userAnchorRS:
                            anchor_ids.append(n['anchor_id'])
                            if i == 0:
                                anchor_names += n['anchor_id__anchor_name']
                                region += n['location']
                            else:
                                anchor_names += ', ' + n['anchor_id__anchor_name']
                                region += ', ' + n['location']
                            i = i + 1

                            insert_array.append({
                                "cmd_value": requestData['cmd_value'],
                                "cmd_type": requestData['cmd_type'],
                                "region": n['location'],
                                "user_anchor_id": n['id'],
                                "anchors": str(n['anchor_id__anchor_id']).split(),
                                "run_time": requestData['run_time'],
                                "time_unit": requestData['time_unit'],
                                "run_count": requestData['run_count'],
                                "interval_unit": requestData['interval_unit'],
                                "interval_time": requestData['interval_time'],
                                "hosts": str(hosts).split(),
                                "host_id": domainQs.id,
                                "host_name": domainQs.domain_name,
                                "host_ip": domainQs.domain_ip,
                                "zone_id": ",".join(str(x) for x in requestData['zone_id']),
                                "zone_area_name": an.user_zone_name,
                                "anchor_id": n['anchor_id'],
                                "host_group_id": '',
                                "lease_id": n['lease_id'],
                                "anchor_names": n['anchor_id__anchor_name'],
                                "user_id": n['user_id']
                            })
        # print('############## Insert Execution Anchor Id ###############', anchor_ids)
        # print('############## Insert Execution Anchor Name ###############', anchor_names)
        print('############## Insert Execution region ###############', region)

        if requestData:
            execution_end_date = timezone.now() + timedelta(minutes=int(requestData['run_time']))
            obj = CommendExecutionHistory.objects.create(
                user_id=user_id,
                commend_query_id='',
                commend_request_payload=requestData,
                host_ids=host_ids,
                host_name=host_name,
                hosts=hosts,
                anchor_ids=anchor_ids,
                anchor_names=anchor_names,
                query=query,
                region=region,
                zone_area_name=zone_names,
                query_status=requestData['query_status'],
                query_type=requestData['type_fo_query'],
                created_date=timezone.now(),
                modified_date=timezone.now(),
                query_execution_end_date=execution_end_date,
                query_execution_interval_unit=requestData['interval_unit'],
                query_execution_interval_time=requestData['interval_time']
            )
            if obj:
                # result = save_history_details(requestData)
                # print(result)
                if len(insert_array) > 0:
                    for dataset in insert_array:
                        ## Insert data in CommendExecutionHistoryDetails table
                        # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', dataset['user_anchor_id'])
                        # print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', obj.id)

                        # print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', dataset['host_id'])
                        # print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', dataset['host_name'])
                        # print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', dataset['host_ip'])
                        # print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', dataset['zone_id'])
                        # print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', dataset['zone_area_name'])
                        # print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', dataset['anchor_id'])

                        chieldObj = CommendExecutionHistoryDetails.objects.create(
                            user_id=user_id,
                            commend_execution_history_id=obj.id,
                            user_anchor_id=dataset['user_anchor_id'],
                            anchor_name=dataset['anchor_names'],
                            host_id=dataset['host_id'],
                            host_name=dataset['host_name'],
                            host_ip=dataset['host_ip'],
                            zone_id=dataset['zone_id'],
                            zone_area_name=dataset['zone_area_name'],
                            anchor_id=dataset['anchor_id'],
                            commend_query_id='',
                            query_status=requestData['query_status'],
                            commend_request_payload=dataset,
                            query_execution_interval_unit=dataset['interval_unit'],
                            query_execution_interval_time=dataset['interval_time'],
                            created_date=timezone.now(),
                            modified_date=timezone.now(),
                        )

                        dataset['parent_id'] = obj.id
                        dataset['chield_id'] = chieldObj.id
            response_data['status'] = 1
            response_data['serialize_obj'] = insert_array
            response_data['message'] = 'History save successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['serialize_obj'] = []
            response_data['message'] = 'History save failure.'
            return JsonResponse(response_data, status=200)


class TraceRouteCommandHistoryWithZoneOrAnchorView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = dict(request.data)
        execution_end_date = timezone.now()
        execution_end_date = timezone.now()
        # print('############## Insert Execution Record ###############', requestData)
        # print('############## Insert Execution Record ###############', requestData['cmd_value'])
        host_ids = []
        host_name = ''
        hosts = ''
        anchor_ids = []
        region = ''
        anchor_names = ''
        zone_id = []
        zone_names = ''
        query = requestData['cmd_value']
        insert_array = []
        ## Get Domain Details
        if requestData['host_id']:
            domainQs = UsersDomain.objects.filter(id=requestData['host_id']).first()
            # domainQs = domainQs.values('id', 'domain_name', 'domain_ip')
            if domainQs:
                host_name += domainQs.domain_name
                hosts += domainQs.domain_ip
                host_ids.append(domainQs.id)

            print('############## Insert Execution Host Id ###############', host_ids)
            # print('############## Insert Execution Host Name ###############', host_name)
            # print('############## Insert Execution Hosts ###############', hosts)
            # print('############## Insert Execution query ###############', query)
        # Get Anchor Details
        if len(requestData['anchor_id']) > 0:
            userAnchorRS = UserAnchor.objects.filter(id__in=requestData['anchor_id'])
            userAnchorRS = userAnchorRS.values('id', 'location', 'anchor_id__anchor_name', 'anchor_id__anchor_id',
                                               'anchor_id', 'lease_id')
            if userAnchorRS:
                for anchor in userAnchorRS:
                    anchor_names = anchor['anchor_id__anchor_name']
                    region = anchor['location']
                    anchor_ids.append(anchor['anchor_id'])
                    insert_array.append({
                        "cmd_value": requestData['cmd_value'],
                        "cmd_type": requestData['cmd_type'],
                        "region": region,
                        "user_anchor_id": anchor['id'],
                        "anchors": str(anchor['anchor_id__anchor_id']).split(),
                        "run_time": requestData['run_time'],
                        "time_unit": requestData['time_unit'],
                        "run_count": requestData['run_count'],
                        "hosts": hosts,
                        "host_group_id": '',
                        "lease_id": anchor['lease_id'],
                        "anchor_names": anchor_names
                    })
        # Get Anchor Details From Zone
        if len(requestData['zone_id']) > 0:
            userZoneRS = UsersZone.objects.filter(id__in=requestData['zone_id'])
            if userZoneRS:
                for an in userZoneRS:
                    userAnchorRS = UserAnchor.objects.filter(id__in=an.user_anchor_ids)
                    userAnchorRS = userAnchorRS.values('id', 'location', 'anchor_id__anchor_name',
                                                       'anchor_id__anchor_id', 'anchor_id', 'lease_id')
                    if userAnchorRS:
                        i = 0
                        for n in userAnchorRS:
                            anchor_ids.append(n['anchor_id'])
                            if i == 0:
                                anchor_names += n['anchor_id__anchor_name']
                                region += n['location']
                            else:
                                anchor_names += ', ' + n['anchor_id__anchor_name']
                                region += ', ' + n['location']
                            i = i + 1

                            insert_array.append({
                                "cmd_value": requestData['cmd_value'],
                                "cmd_type": requestData['cmd_type'],
                                "region": n['location'],
                                "user_anchor_id": n['id'],
                                "anchors": str(n['anchor_id__anchor_id']).split(),
                                "run_time": requestData['run_time'],
                                "time_unit": requestData['time_unit'],
                                "run_count": requestData['run_count'],
                                "hosts": hosts,
                                "host_group_id": '',
                                "lease_id": n['lease_id'],
                                "anchor_names": n['anchor_id__anchor_name']
                            })
        print('############## Insert Execution Anchor Id ###############', anchor_ids)
        # print('############## Insert Execution Anchor Name ###############', anchor_names)
        # print('############## Insert Execution region ###############', region)
        if requestData:
            execution_end_date = timezone.now() + timedelta(minutes=int(requestData['run_time']))
            obj = CommendExecutionHistory.objects.create(
                user_id=user_id,
                commend_query_id='',
                commend_request_payload=requestData,
                host_ids=host_ids,
                host_name=host_name,
                hosts=hosts,
                anchor_ids=anchor_ids,
                anchor_names=anchor_names,
                query=query,
                region=region,
                query_type=requestData['type_fo_query'],
                created_date=timezone.now(),
                modified_date=timezone.now(),
                query_execution_end_date=execution_end_date
            )
            if obj:
                # result = save_history_details(requestData)
                # print(result)
                if len(insert_array) > 0:
                    for dataset in insert_array:
                        ## Insert data in CommendExecutionHistoryDetails table
                        # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', dataset['user_anchor_id'])
                        print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', obj.id)
                        chieldObj = CommendExecutionHistoryDetails.objects.create(
                            user_id=user_id,
                            commend_execution_history_id=obj.id,
                            user_anchor_id=dataset['user_anchor_id'],
                            anchor_name=dataset['anchor_names'],
                            commend_query_id='',
                            commend_request_payload=dataset,
                            created_date=timezone.now(),
                            modified_date=timezone.now(),
                        )

                        dataset['parent_id'] = obj.id
                        dataset['chield_id'] = chieldObj.id
            response_data['status'] = 1
            response_data['serialize_obj'] = insert_array
            response_data['message'] = 'History save successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['serialize_obj'] = []
            response_data['message'] = 'History save failure.'
            return JsonResponse(response_data, status=200)


class DnsQueryCommandHistoryWithZoneOrAnchorView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = dict(request.data)
        execution_end_date = timezone.now()
        execution_end_date = timezone.now()
        # print('############## Insert Execution Record ###############', requestData)
        print('############## Insert Execution Record ###############', requestData['cmd_value'])
        # return JsonResponse(response_data, status=200)
        host_ids = []
        host_name = ''
        hosts = ''
        host_id = 0
        anchor_ids = []
        region = ''
        anchor_names = ''
        zone_id = []
        zone_names = ''
        query = requestData['cmd_value']
        insert_array = []
        ## Get Domain Details
        if requestData['host_ip']:
            domainQs = UsersDomain.objects.filter(domain_ip=requestData['host_ip']).first()
            # domainQs = domainQs.values('id', 'domain_name', 'domain_ip')
            if domainQs:
                host_name += domainQs.domain_name
                hosts += domainQs.domain_ip
                host_id = domainQs.id
                host_ids.append(domainQs.id)

            print('############## Insert Execution Host Id ###############', host_ids)
            # print('############## Insert Execution Host Name ###############', host_name)
            # print('############## Insert Execution Hosts ###############', hosts)
            # print('############## Insert Execution query ###############', query)
        # Get Anchor Details
        if len(requestData['anchor_id']) > 0:
            userAnchorRS = UserAnchor.objects.filter(id__in=requestData['anchor_id'])
            userAnchorRS = userAnchorRS.values('id', 'location', 'anchor_id__anchor_name', 'anchor_id__anchor_id',
                                               'anchor_id', 'lease_id')
            if userAnchorRS:
                for anchor in userAnchorRS:
                    anchor_names += anchor['anchor_id__anchor_name']
                    region = anchor['location']
                    anchor_ids.append(anchor['anchor_id'])
                    insert_array.append({
                        "cmd_value": requestData['cmd_value'],
                        "cmd_type": requestData['cmd_type'],
                        "query_type": requestData['query_type'],
                        "region": region,
                        "user_anchor_id": anchor['id'],
                        "anchors": str(anchor['anchor_id__anchor_id']).split(),
                        "run_time": requestData['run_time'],
                        "run_count": requestData['run_count'],
                        "time_unit": requestData['time_unit'],
                        "hosts": requestData['host_ip'],
                        "host_id": host_id,
                        "host_name": host_name,
                        "dns_query_type": requestData['query_type'],
                        "host_group_id": '',
                        "lease_id": anchor['lease_id'],
                        "anchor_names": anchor_names
                    })
        # Get Anchor Details From Zone
        if len(requestData['zone_id']) > 0:
            userZoneRS = UsersZone.objects.filter(id__in=requestData['zone_id'])
            if userZoneRS:
                for an in userZoneRS:
                    zone_names = an.user_zone_name
        print('############## Insert Execution Anchor Id ###############', anchor_ids)
        # print('############## Insert Execution Anchor Name ###############', anchor_names)
        # print('############## Insert Execution region ###############', region)
        if requestData:
            execution_end_date = timezone.now() + timedelta(minutes=int(requestData['run_time']))
            obj = CommendExecutionHistory.objects.create(
                user_id=user_id,
                commend_query_id='',
                commend_request_payload=requestData,
                host_ids=host_ids,
                host_name=host_name,
                hosts=hosts,
                anchor_ids=anchor_ids,
                anchor_names=anchor_names,
                zone_area_name=zone_names,
                query=query,
                region=region,
                query_type=requestData['type_fo_query'],
                dnsquery_type=requestData['query_type'],
                created_date=timezone.now(),
                modified_date=timezone.now(),
                query_execution_end_date=execution_end_date
            )
            if obj:
                # result = save_history_details(requestData)
                # print(result)
                if len(insert_array) > 0:
                    for dataset in insert_array:
                        ## Insert data in CommendExecutionHistoryDetails table
                        # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', dataset['user_anchor_id'])
                        # print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', obj.id)
                        chieldObj = CommendExecutionHistoryDetails.objects.create(
                            user_id=user_id,
                            commend_execution_history_id=obj.id,
                            user_anchor_id=dataset['user_anchor_id'],
                            anchor_name=dataset['anchor_names'],
                            dnsquery_type=requestData['query_type'],
                            anchor_id=','.join(str(x) for x in anchor_ids),
                            host_id=dataset['host_id'],
                            host_name=dataset['host_name'],
                            host_ip=dataset['hosts'],
                            commend_query_id='',
                            commend_request_payload=dataset,
                            created_date=timezone.now(),
                            modified_date=timezone.now(),
                        )

                        dataset['parent_id'] = obj.id
                        dataset['chield_id'] = chieldObj.id

            # result = save_history_details(requestData)
            # print(result)
            # if len(insert_array) > 0:
            #     i = 1
            #     for dataset in insert_array:
            #         ## Insert data in CommendExecutionHistoryDetails table
            #         print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', dataset['user_anchor_id'])
            #         # print('&&&&&&&&&&&&&&&&&&&&&&&& PARENT ID &&&&&&&&&&&&&&&&&&&&&&&&', obj.id)
            #         # chieldObj = CommendExecutionHistoryDetails.objects.create(
            #         #         user_id=user_id,
            #         #         commend_execution_history_id=obj.id,
            #         #         user_anchor_id=dataset['user_anchor_id'],
            #         #         anchor_name=dataset['anchor_names'],
            #         #         commend_query_id='',
            #         #         commend_request_payload=dataset,
            #         #         created_date=timezone.now(),
            #         #         modified_date=timezone.now(),
            #         #     )

            #         dataset['parent_id'] = 1
            #         dataset['chield_id'] = i
            #         i = i+1

            response_data['status'] = 1
            response_data['serialize_obj'] = insert_array
            response_data['message'] = 'History save successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['serialize_obj'] = []
            response_data['message'] = 'History save failure.'
            return JsonResponse(response_data, status=200)


class GroupCommandHistoryView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        response_data = {}

        token, created = Token.objects.get_or_create(user=user)  ### Get user authentication token
        token_data = token.key  ### if it is first login then create token first and get token
        # rs=CommendExecutionHistory.objects.filter(user_id=user_id, is_deleted=False).order_by('-id')
        # if rs:
        #     serializer = CommandHitRequestHistorySerializer(rs, many=True)
        #     response_data['status'] = 1
        #     response_data['message'] = 'History list.'
        #     response_data['history'] = serializer.data
        #     return JsonResponse(response_data, status=200)
        # else:
        #     response_data['status'] = 1
        #     response_data['message'] = 'History list blank.'
        #     response_data['history'] = []
        #     return JsonResponse(response_data, status=200)
        response_data['status'] = 1
        response_data['message'] = 'History list.'
        response_data['query_id'] = get_random_string(length=50)
        return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = dict(request.data)
        execution_end_date = timezone.now()
        execution_end_date = timezone.now()
        # print('############## Insert Execution Record ###############', requestData)
        # print('############## Insert Execution Record ###############', requestData['cmd_value'])
        host_ids = []
        host_name = ''
        hosts = ''
        service_id = requestData['service_ids']
        service_name = ''
        service_domain_ids = []
        anchor_ids = []
        anchor_names = ''
        query = requestData['cmd_value']
        ## Get Service Details
        serviceQs = UsersHostGroup.objects.filter(id__in=requestData['service_ids'])
        if serviceQs:
            for ser in serviceQs:
                service_name = ser.host_group_name
        ## Get Domain Details
        hostGroupQs = UsersHostGroupDomain.objects.filter(user_host_group_id__in=requestData['service_ids'])
        hostGroupQs = hostGroupQs.values('id', 'domain_id', 'domain_id__domain_name', 'domain_id__domain_ip')
        if hostGroupQs:
            i = 0
            for domain in hostGroupQs:
                host_ids.append(domain['domain_id'])
                service_domain_ids.append(domain['domain_id'])
                if i == 0:
                    host_name += domain['domain_id__domain_name']
                    hosts += domain['domain_id__domain_ip']
                else:
                    host_name += ', ' + domain['domain_id__domain_name']
                    hosts += ', ' + domain['domain_id__domain_ip']
                i = i + 1

            print('############## Insert Execution Host Id ###############', host_ids)
            # print('############## Insert Execution Host Name ###############', host_name)
            # print('############## Insert Execution Hosts ###############', hosts)
            # print('############## Insert Execution query ###############', query)
        # Get Anchor Details
        userAnchorRS = UserAnchor.objects.filter(id__in=requestData['anchor_ids'])
        if userAnchorRS:
            j = 0
            for an in userAnchorRS:
                # print('Anchor Ids RESULT', n.anchor_id)
                anchorRS = Anchor.objects.filter(id=an.anchor_id).first()
                if anchorRS:
                    anchor_ids.append(anchorRS.id)
                    if j == 0:
                        anchor_names += anchorRS.anchor_name
                    else:
                        anchor_names += ', ' + anchorRS.anchor_name
                    j = j + 1
        # print('############## Insert Execution Host Id ###############', host_ids)
        # print('############## Insert Execution Host Name ###############', host_name)
        # print('############## Insert Execution Host ###############', hosts)
        print('############## Insert Execution Anchor Id ###############', anchor_ids)
        # print('############## Insert Execution Anchor Name ###############', anchor_names)
        # print('############## Insert Execution region ###############', region)

        # response_data['status'] = 1
        # response_data['serialize_obj'] = []
        # response_data['message'] = 'History save successfully.'
        # return JsonResponse(response_data, status=200)

        if requestData:
            execution_end_date = timezone.now() + timedelta(minutes=int(requestData['run_time']))
            obj = CommendExecutionHistory.objects.create(
                user_id=user_id,
                commend_query_id='',
                commend_request_payload=requestData,
                host_ids=host_ids,
                host_name=host_name,
                hosts=hosts,
                service_id=service_id,
                service_name=service_name,
                service_domain_ids=service_domain_ids,
                anchor_ids=anchor_ids,
                anchor_names=anchor_names,
                query=query,
                query_type=requestData['cmd_type'],
                created_date=timezone.now(),
                modified_date=timezone.now(),
                query_execution_end_date=execution_end_date
            )
            if obj:
                result = save_history_details(requestData)
                # print(result)
                if len(result) > 0:
                    for dataset in result:
                        ## Insert data in CommendExecutionHistoryDetails table
                        chieldObj = CommendExecutionHistoryDetails.objects.create(
                            user_id=user_id,
                            commend_execution_history_id=obj.id,
                            users_host_group_id=dataset['host_group_id'],
                            users_zone_id=dataset['zone_id'],
                            user_anchor_id=dataset['user_anchor_id'],
                            commend_query_id='',
                            commend_request_payload=dataset,
                            created_date=timezone.now(),
                            modified_date=timezone.now(),
                        )
                        dataset['parent_id'] = obj.id
                        dataset['chield_id'] = chieldObj.id
            response_data['status'] = 1
            response_data['serialize_obj'] = result
            response_data['message'] = 'History save successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['serialize_obj'] = []
            response_data['message'] = 'History save failure.'
            return JsonResponse(response_data, status=200)

    def put(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        update_success_ids = []
        update_failure_ids = []
        # is_view 	= request.data.get('is_view', None)
        requestData = request.data

        # rs = CommendExecutionHistory.objects.filter(id=requestData['id'])
        # if rs:
        #     if is_view is not None:
        #         CommendExecutionHistory.objects.filter(id=requestData['id']).update(has_been_seen=True)
        #     else: 
        #         CommendExecutionHistory.objects.filter(id=requestData['id']).update(commend_query_id=requestData['query_id'], server_hit_status=requestData['status'])
        #     response_data['status'] = 1
        #     response_data['message'] = 'History update successfully.'
        #     return JsonResponse(response_data, status=200)
        # else:
        #     response_data['status'] = 0
        #     response_data['message'] = 'History update failure.'
        #     return JsonResponse(response_data, status=200)
        if len(requestData) > 0:
            query_status = 'running'
            parent_id = 0
            for data in requestData['update_set']:
                query_status = data['status']
                parent_id = data['parent_id']
                print(data['chield_id'])
                rs = CommendExecutionHistoryDetails.objects.filter(id=data['chield_id'], user_id=user_id,
                                                                   commend_execution_history_id=data['parent_id'])
                if rs:
                    CommendExecutionHistoryDetails.objects.filter(id=data['chield_id'], user_id=user_id,
                                                                  commend_execution_history_id=data[
                                                                      'parent_id']).update(
                        commend_query_id=data['query_id'], server_hit_status=data['status'])
                    update_success_ids.append({"parent_id": data['parent_id'], "chield_id": data['chield_id']})
                else:
                    update_failure_ids.append({"parent_id": data['parent_id'], "chield_id": data['chield_id']})
            qs = CommendExecutionHistory.objects.filter(id=parent_id).update(server_hit_status=query_status,
                                                                             query_status=query_status)
            if len(update_success_ids) > 0:
                response_data['status'] = 1
                response_data['success_ids'] = update_success_ids
                response_data['failure_ids'] = update_failure_ids
                response_data['message'] = 'History update successfully.'
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['success_ids'] = update_success_ids
                response_data['failure_ids'] = update_failure_ids
                response_data['message'] = 'History update failure.'
                return JsonResponse(response_data, status=200)


def save_history_details(request):
    set_cmd_value = request['cmd_value']
    set_cmd_type = request['cmd_type']
    set_region = ''
    set_zone_id = ''
    set_run_time = request['run_time']
    set_time_unit = request['time_unit']
    set_run_count = request['run_count']
    set_hosts = []
    set_host_group_id = ''
    insert_array = []
    if len(request['service_ids']) > 0:
        for service_id in request['service_ids']:
            rs = UsersHostGroupDomain.objects.filter(user_host_group_id=service_id, is_deleted=False)
            if rs:
                serializer = UserHostGroupDomainViewSerializer(rs, many=True)
                for domain in serializer.data:
                    # print('#### Domain ID #####', domain['domain']['domain_ip'])
                    set_hosts = []
                    set_hosts.append(domain['domain']['domain_ip'])
                    set_host_group_id = service_id
                    if len(request['zone_ids']) > 0:
                        for zone_id in request['zone_ids']:
                            zoneObj = UsersZoneAreaDetails.objects.filter(user_zone_id=zone_id, is_deleted=False)
                            if zoneObj:
                                zoneserializer = AreaDetailsViewSerializer(zoneObj, many=True)
                                for zone in zoneserializer.data:
                                    # print('&&&&&& Zone Name &&&&&', zone['area_name'])
                                    # insert_array.update(region=zone['area_name'])
                                    insert_array.append(
                                        {
                                            "cmd_value": set_cmd_value,
                                            "cmd_type": set_cmd_type,
                                            "region": zone['area_name'],
                                            "zone_id": zone_id,
                                            "user_anchor_id": '',
                                            "anchor": [],
                                            "run_time": set_run_time,
                                            "time_unit": set_time_unit,
                                            "run_count": set_run_count,
                                            "hosts": set_hosts,
                                            "host_group_id": set_host_group_id
                                        }
                                    )
                    if len(request['anchor_ids']) > 0:
                        # print("&&&&&& request['anchor_ids'] &&&&&&&", request['anchor_ids'])
                        anchorObj = UserAnchor.objects.filter(id__in=list(request['anchor_ids']), is_deleted=False)
                        # print("QUERY*********************", anchorObj.count())
                        if anchorObj:
                            # print("QUERY", anchorObj.query)
                            useranchorserializer = UserAnchorSerializer(anchorObj, many=True)
                            # print('&&&&&& useranchorserializer &&&&&&&', useranchorserializer)
                            for anchor in useranchorserializer.data:
                                set_anchors = []
                                set_anchors.append(anchor['aiori_anchor_id'])
                                insert_array.append(
                                    {
                                        "cmd_value": set_cmd_value,
                                        "cmd_type": set_cmd_type,
                                        "region": anchor['location'],
                                        "zone_id": '',
                                        "user_anchor_id": anchor['id'],
                                        "anchors": set_anchors,
                                        "run_time": set_run_time,
                                        "time_unit": set_time_unit,
                                        "run_count": set_run_count,
                                        "hosts": set_hosts,
                                        "host_group_id": set_host_group_id
                                    }
                                )
                return insert_array


def get_aiori_status_and_update_command_detaild(user_id, history_id):
    history_detail_rs = CommendExecutionHistoryDetails.objects.filter(user_id=user_id,
                                                                      commend_execution_history_id=history_id)
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json", "apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    if history_detail_rs:
        for item in history_detail_rs:
            # query = str(settings.AIORI_ANCHOR_HOST) + ":" + str(settings.AIORI_ANCHOR_PORT) + str(settings.AIORI_ANCHOR_URL) + item.commend_query_id
            query = str(settings.AIORI_ANCHOR_HOST) + str(settings.AIORI_ANCHOR_URL) + item.commend_query_id
            # print('*************** commend_query *******************', query)
            # print('*************** commend_query_id *******************', item.commend_query_id)
            result = requests.get(query, headers=set_headers)
            if result.status_code == 200:
                json_result = result.json()
                print('*************** json_result *******************', json_result['status'])
                CommendExecutionHistoryDetails.objects.filter(commend_query_id=json_result['id']).update(
                    aiori_query_status=json_result['status'])
        return 1
    else:
        return 0


class GroupCommandHistoryDetailsView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        # user_id = user.id
        # print("User id details.....................................", user_id)
        provided_user_id = request.data.get('user_id') or request.query_params.get('user_id')

        if provided_user_id:
            try:
                user_id = int(provided_user_id)
            except ValueError:
                return JsonResponse({'status': 0, 'message': 'Invalid user_id format'}, status=400)
        else:
            user_id = request.user.id

        print("Using User ID:", user_id)
        response_data = {}
        requestData = request.data
        get_aiori_status_and_update_command_detaild(user_id, requestData['history_id'])
        if user.is_faculty:
            rs = CommendExecutionHistory.objects.filter(is_deleted=False,
                                                        id=requestData['history_id']).first()
        else:
            rs = CommendExecutionHistory.objects.filter(user_id=user_id, is_deleted=False,
                                                        id=requestData['history_id']).first()
        print("RS data...............................................", rs)
        if rs:
            serializer = CommandHistoryDetailsSerializer(rs)
            response_data['status'] = 1
            response_data['message'] = 'History details.'
            response_data['history'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 1
            response_data['message'] = 'History details blank.'
            response_data['history'] = []
            return JsonResponse(response_data, status=200)

    def put(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data

        rs = CommendExecutionHistory.objects.filter(id=requestData['id'])
        if rs:
            CommendExecutionHistory.objects.filter(id=requestData['id']).update(
                check_points_status=requestData['use_point_status'], server_hit_status=requestData['status'])
            history_detail_rs = CommendExecutionHistoryDetails.objects.filter(user_id=user_id,
                                                                              commend_execution_history_id=requestData[
                                                                                  'id'])
            if history_detail_rs:
                CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=requestData['id']).update(
                    check_points_status=requestData['use_point_status'], server_hit_status=requestData['status'])
            response_data['status'] = 1
            response_data['message'] = 'History update successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'History update failure.'
            return JsonResponse(response_data, status=200)


def QueryHistoryStatusUpdateCorn():
    response_data = {}
    # print('QueryHistoryStatusUpdateCorn')
    # print('Time Zone', timezone.now())
    # rs = CommendExecutionHistory.objects.filter(is_blocked=False, query_execution_end_date<=timezone.now())
    rs = CommendExecutionHistory.objects.filter(is_blocked=False, is_deleted=False, check_points_status='success',
                                                query_execution_end_date__lte=timezone.now(),
                                                query_status='running').values_list('id', flat=True).order_by('id')
    # print('Return', rs)
    if rs:
        for hisid in list(rs):
            # print('*** ID ***', hisid)
            comHisCount = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=hisid,
                                                                        query_status='running').count()
            # print('*** comHisCount ***', comHisCount)
            if comHisCount > 0:
                CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=hisid,
                                                              query_status='running').update(query_status='close')
        query = CommendExecutionHistory.objects.filter(id__in=list(rs)).update(query_status='close')
        # serializer = CommandHitRequestHistorySerializer(query, many=True)
        # response_data['status'] = 1
        # response_data['message'] = 'History update successfully.'
        # response_data['Date Time Now'] = timezone.now()
        # response_data['data'] = list(rs)
        # return JsonResponse(response_data, status=200)
        return 'Success'
    else:
        # response_data['status'] = 0
        # response_data['message'] = 'History update successfully.'
        # response_data['data'] = []
        # return JsonResponse(response_data, status=200)
        return 'failure'


class CommandHistoryDetailsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, historyid):
        user = request.user
        user_id = user.id
        history_id = historyid
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(user_id=user_id, is_deleted=False, check_points_status='success',
                                                    id=history_id).first()
        if rs:
            qs = UserAnchor.objects.filter(is_deleted=False, id=rs.commend_request_payload['anchor_ids']).first()
            # print('&&&&&',rs.commend_request_payload['anchor_ids'])
            # serializer = QueryReportsSerializer(rs)
            data = {
                "query_id": rs.commend_query_id,
                "latitude": qs.latitude,
                "longitude": qs.longitude,
                "location": qs.location
            }
            response_data['status'] = 1
            response_data['message'] = 'History list.'
            # response_data['history'] = serializer.data
            response_data['history'] = data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 1
            response_data['message'] = 'History list blank.'
            response_data['history'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(user_id=user_id, is_deleted=False, check_points_status='success',
                                                    id=requestData['history_id']).first()
        if rs:
            qs = UserAnchor.objects.filter(is_deleted=False, id=rs.commend_request_payload['anchor_ids']).first()
            history_data = {
                "query_id": rs.commend_query_id,
                "anchor": rs.anchor_names,
                "host_name": rs.host_name,
                "latitude": qs.latitude,
                "longitude": qs.longitude,
                "location": qs.location
            }
            response_data['status'] = 1
            response_data['message'] = 'History list.'
            response_data['history'] = history_data
            response_data['traceroute'] = []
            response_data['map_data'] = []
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 1
            response_data['message'] = 'History list blank.'
            response_data['history'] = []
            return JsonResponse(response_data, status=200)


def pin_request_in_rd3mn(arr):
    # print('&&&&&&&&&&&&&&&&&&&&', arr)
    commend_execution_history_ids = []
    commend_execution_history_obj = []
    commend_execution_history_details_obj = []
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json", "apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    interval_in_second = 10
    if len(arr) > 0:
        for x in arr:
            if x['query_execution_interval_unit'] == 'second':
                interval_in_second = int(x['query_execution_interval_time'])
            if x['query_execution_interval_unit'] == 'minute':
                interval_in_second = int(x['query_execution_interval_time']) * 60
            if x['query_execution_interval_unit'] == 'hour':
                interval_in_second = int(x['query_execution_interval_time']) * 60 * 60

            # url = str(x['user_anchor_id__anchor_id__server_url']) + "ping/?lease_id=" + x['commend_request_payload']['lease_id']
            url = str(x['user_anchor_id__anchor_id__server_url']) + "ping/?lease_id=" + x['commend_request_payload'][
                'lease_id'] + "&interval=" + str(interval_in_second)
            data = {
                "cmd_value": x['commend_request_payload']['cmd_value'],
                "cmd_type": x['commend_request_payload']['cmd_type'],
                "run_time": x['commend_request_payload']['run_time'],
                "run_count": x['commend_request_payload']['run_count'],
                "region": x['commend_request_payload']['region'].lower(),
                "hosts": x['commend_request_payload']['hosts'],
                "anchors": x['commend_request_payload']['anchors']
            }
            # print('&&&&&&&&&&&&&&&&&&& url VALUE &&&&&&&&&&&&&&&&&&&&', url)
            # print('&&&&&&&&&&&&&&&&&&& data VALUE &&&&&&&&&&&&&&&&&&&&', data)
            runtine_minute = int(x['commend_request_payload']['run_time'])
            execution_end_date = timezone.now() + timedelta(minutes=runtine_minute)
            # print('&&&&&&&&&&&&&&&&&&& query_execution_end_date VALUE &&&&&&&&&&&&&&&&&&&&', execution_end_date)
            result = requests.post(url, json=data, headers=set_headers)
            # print('&&&&&&&&&&&&&&&&&&& result.status_code &&&&&&&&&&&&&&&&&&&&', result.status_code)
            # print('&&&&&&&&&&&&&&&&&&& x commend_execution_history_id &&&&&&&&&&&&&&&&&&&&', x['commend_execution_history_id'])
            # print('&&&&&&&&&&&&&&&&&&& x id &&&&&&&&&&&&&&&&&&&&', x['id'])

            if result.status_code == 200:
                json_result = result.json()
                # print('&&&&&&&&&&&&&&&&&&& json_result id &&&&&&&&&&&&&&&&&&&&', json_result['id'])
                if len(commend_execution_history_ids) > 0:
                    if x['commend_execution_history_id'] not in commend_execution_history_ids:
                        commend_execution_history_ids.append(x['commend_execution_history_id'])
                        commend_execution_history_obj.append(
                            {'commend_execution_history_id': x['commend_execution_history_id'],
                             'query_status': 'running', 'query_execution_end_date': execution_end_date})
                else:
                    commend_execution_history_ids.append(x['commend_execution_history_id'])
                    commend_execution_history_obj.append(
                        {'commend_execution_history_id': x['commend_execution_history_id'], 'query_status': 'running',
                         'query_execution_end_date': execution_end_date})
                commend_execution_history_details_obj.append(
                    {'commend_execution_history_detail_id': x['id'], 'commend_query_id': json_result['id'],
                     'query_status': 'running',
                     'commend_execution_history_details_execution_end_date': execution_end_date})
                print(json_result['id'])

        #     if len(commend_execution_history_ids) > 0:
        #         if x['commend_execution_history_id'] not in commend_execution_history_ids:
        #             commend_execution_history_ids.append(x['commend_execution_history_id'])
        #             commend_execution_history_obj.append({'commend_execution_history_id':x['commend_execution_history_id'], 'query_status': 'running', 'query_execution_end_date': execution_end_date})
        #     else:
        #         commend_execution_history_ids.append(x['commend_execution_history_id'])
        #         commend_execution_history_obj.append({'commend_execution_history_id':x['commend_execution_history_id'], 'query_status': 'running', 'query_execution_end_date': execution_end_date})
        #     commend_execution_history_details_obj.append({'commend_execution_history_detail_id': x['id'], 'commend_query_id': '11222245687', 'query_status': 'running', 'commend_execution_history_id':x['commend_execution_history_id']})

        # print('&&&&&&&&&&&&&&&&&&& commend_execution_history_obj &&&&&&&&&&&&&&&&&&&&', commend_execution_history_obj)
        # print('&&&&&&&&&&&&&&&&&&& commend_execution_history_details_obj &&&&&&&&&&&&&&&&&&&&', commend_execution_history_details_obj)
        ##### Update Command Execution History Record #####
        if len(commend_execution_history_obj) > 0:
            for c in commend_execution_history_obj:
                CommendExecutionHistory.objects.filter(pk=c['commend_execution_history_id']).update(
                    query_status=c['query_status'], query_execution_end_date=c['query_execution_end_date'])
                # print('&&&&&&&&&&&&&&&&&&& Update CommendExecutionHistory Id &&&&&&&&&&&&&&&&&&&&', c['commend_execution_history_id'])
        ##### Update Command Execution History Details Record #####
        if len(commend_execution_history_details_obj) > 0:
            for ch in commend_execution_history_details_obj:
                CommendExecutionHistoryDetails.objects.filter(pk=ch['commend_execution_history_detail_id']).update(
                    commend_query_id=ch['commend_query_id'], query_status=ch['query_status'],
                    created_date=timezone.now(),
                    modified_date=ch['commend_execution_history_details_execution_end_date'])
                # print('&&&&&&&&&&&&&&&&&&& Update Commend Execution History Details Id &&&&&&&&&&&&&&&&&&&&', ch['commend_execution_history_detail_id'])


def merge_x_and_y(x_data, y_data):
    result = [a.copy() for a in x_data]
    [a.update(b) for a, b in zip(result, y_data)]
    return result


class RD3MNCommandExecutionView(APIView):
    # permission_classes = (IsAuthenticated,)
    def get(self, request):
        from django.db.models import ExpressionWrapper, F
        user = request.user
        user_id = user.id
        response_data = {}
        graterThenNineExecutionAnchorNameArray = []
        lessThenNineExecutionAnchorNameArray = []
        test_arr = []
        final_arr = []
        filter_execution_arr = []
        new_arr = []
        short_array = []
        # hisobj = Users.objects.filter(username='sunil.sharma@stpi.in').update(username='sunil.sharma123@stpi.in', email='sunil.sharma123@stpi.in')
        # anchor_host_rs = CommendExecutionHistoryDetails.objects.filter(query_status='enqueue', anchor_name='IN-4')
        # anchor_host_rs = anchor_host_rs.values('id', 'commend_request_payload', 'commend_execution_history_id')
        # anchor_host_rs = anchor_host_rs.order_by('-id')

        # response_data['status'] = 1
        # response_data['message'] = 'History list.'
        # response_data['union'] = list(anchor_host_rs)
        # return JsonResponse(response_data, status=200)

        # response_data['status'] = 1
        # response_data['message'] = 'History list.'
        # return JsonResponse(response_data, status=200)
        request_load_limit_per_anchor = 12
        anchor_host_rs = CommendExecutionHistoryDetails.objects.filter(query_status='enqueue',
                                                                       anchor_name__isnull=False,
                                                                       commend_execution_history_id__query='ping')
        anchor_host_rs = anchor_host_rs.values('id', 'anchor_name', 'commend_request_payload',
                                               'user_anchor_id__anchor_id__server_url', 'commend_execution_history_id')
        anchor_host_rs = anchor_host_rs.order_by('id')
        anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-blr-anchor')
        anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-gwh-anchor')
        anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-kol-anchor')
        anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-moh-anchor')
        anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-mum-anchor')
        # anchor_host_rs = anchor_host_rs.annotate(query_count=Count('commend_execution_history_id'))
        if anchor_host_rs:
            # anchor_rs = CommendExecutionHistoryDetails.objects.filter(query_status='running')
            # anchor_rs = anchor_rs.filter(anchor_name__isnull=False)
            # anchor_rs = anchor_rs.values('anchor_name')
            # anchor_rs = anchor_rs.order_by('user_anchor_id')
            # anchor_rs = anchor_rs.exclude(anchor_name ='nats-blr-anchor')
            # anchor_rs = anchor_rs.exclude(anchor_name ='nats-gwh-anchor')
            # anchor_rs = anchor_rs.exclude(anchor_name ='nats-kol-anchor')
            # anchor_rs = anchor_rs.exclude(anchor_name ='nats-moh-anchor')
            # anchor_rs = anchor_rs.exclude(anchor_name ='nats-mum-anchor')
            # anchor_rs = anchor_rs.annotate(anchor_count=Count('user_anchor_id'))
            # # union = merge_x_and_y(list(a_rs), list(b_rs))
            # if anchor_rs:
            #     for an in anchor_rs:
            #         if an['anchor_count'] <= request_load_limit_per_anchor:
            #             # test_arr.append(an['anchor_name'])
            #             test_arr.append(an)
            #             # union.append(an['anchor_name'])
            #             # lessThenNineExecutionAnchorNameArray.append(an)
            #         else:
            #             graterThenNineExecutionAnchorNameArray.append(an)

            # if len(a_rs) > 0:
            #     for x in b_rs:
            #         if x['anchor_name'] not in a_rs:
            #             union.append(x)
            # if len(test_arr) > 0:
            #     for n in anchor_host_rs:
            #         if n['anchor_name'] in test_arr:
            #             final_arr.append(n)
            # else:
            #     final_arr = list(anchor_host_rs)

            # ## New Code Add Dated On: 09-03-2022
            # if len(test_arr) > 0:
            #     for x in test_arr:
            #         filter_anchor_host_rs = CommendExecutionHistoryDetails.objects.filter(query_status='enqueue', anchor_name=x['anchor_name'])
            #         filter_anchor_host_rs = filter_anchor_host_rs.values('id', 'anchor_name', 'commend_request_payload', 'user_anchor_id__anchor_id__server_url', 'commend_execution_history_id')
            #         filter_anchor_host_rs = filter_anchor_host_rs.order_by('id')[:request_load_limit_per_anchor]
            #         print('&&&&&&&&&&&&& filter_anchor_host_rs &&&&&&&&&&&&&', filter_anchor_host_rs.query)
            #         if filter_anchor_host_rs:
            #             for r in filter_anchor_host_rs:
            #                 filter_execution_arr.append(r)

            ## Execute Pin Request In RD3MN Server
            # if len(final_arr) > 0:
            #     pin_request_in_rd3mn(final_arr)
            # new_arr = []
            # for f in final_arr:
            #     if f['anchor_name'] == 'IN-2':
            #         print('Print IN-2', f)
            #         new_arr.append(f)
            #         pin_request_in_rd3mn(new_arr)

            a_rs = CommendExecutionHistoryDetails.objects.filter(Q(query_status='running') | Q(query_status='enqueue'))
            a_rs = a_rs.filter(anchor_name__isnull=False, commend_execution_history_id__query='ping')
            a_rs = a_rs.values('anchor_name')
            a_rs = a_rs.order_by('user_anchor_id')
            a_rs = a_rs.exclude(anchor_name='nats-blr-anchor')
            a_rs = a_rs.exclude(anchor_name='nats-gwh-anchor')
            a_rs = a_rs.exclude(anchor_name='nats-kol-anchor')
            a_rs = a_rs.exclude(anchor_name='nats-moh-anchor')
            a_rs = a_rs.exclude(anchor_name='nats-mum-anchor')
            a_rs = a_rs.annotate(anchor_count=Count('user_anchor_id'))

            if a_rs:
                for r in a_rs:
                    b_rs = CommendExecutionHistoryDetails.objects.filter(query_status='running',
                                                                         anchor_name__isnull=False,
                                                                         anchor_name=r['anchor_name'],
                                                                         commend_execution_history_id__query='ping')
                    b_rs = b_rs.values('anchor_name')
                    b_rs = b_rs.order_by('user_anchor_id')
                    b_rs = b_rs.exclude(anchor_name='nats-blr-anchor')
                    b_rs = b_rs.exclude(anchor_name='nats-gwh-anchor')
                    b_rs = b_rs.exclude(anchor_name='nats-kol-anchor')
                    b_rs = b_rs.exclude(anchor_name='nats-moh-anchor')
                    b_rs = b_rs.exclude(anchor_name='nats-mum-anchor')
                    b_rs = b_rs.annotate(anchor_count=Count('user_anchor_id'))
                    if b_rs:
                        for b in b_rs:
                            new_arr.append(b)
                    else:
                        # print('&&&&&&&&&&&&&&&& ANCHOR NAME IS &&&&&&&&&&&&&&&&&', r['anchor_name'])
                        # print('&&&&&&&&&&&&&&&& ANCHOR COUNT IS &&&&&&&&&&&&&&&&&', r['anchor_count'])
                        new_arr.append({'anchor_name': r['anchor_name'], 'anchor_count': 0})

            if len(new_arr) > 0:
                for na in new_arr:
                    # print('&&&&&&&&&&&&&&&& ANCHOR NAME IS &&&&&&&&&&&&&&&&&', na['anchor_name'])
                    # print('&&&&&&&&&&&&&&&& ANCHOR COUNT IS &&&&&&&&&&&&&&&&&', na['anchor_count'])
                    if na['anchor_count'] <= request_load_limit_per_anchor:
                        short_array.append(na)

            if len(short_array) > 0:
                query_limit = 0
                for x in short_array:
                    query_limit = int(request_load_limit_per_anchor) - int(x['anchor_count'])
                    filter_anchor_host_rs = CommendExecutionHistoryDetails.objects.filter(query_status='enqueue',
                                                                                          anchor_name=x['anchor_name'],
                                                                                          commend_execution_history_id__query='ping')
                    filter_anchor_host_rs = filter_anchor_host_rs.values('id', 'anchor_name', 'commend_request_payload',
                                                                         'user_anchor_id__anchor_id__server_url',
                                                                         'commend_execution_history_id',
                                                                         'query_execution_interval_unit',
                                                                         'query_execution_interval_time')
                    filter_anchor_host_rs = filter_anchor_host_rs.order_by('id')[:query_limit]
                    # print('&&&&&&&&&&&&& filter_anchor_host_rs &&&&&&&&&&&&&', filter_anchor_host_rs.count(), '*****Anchor Name****', x['anchor_name'])
                    if filter_anchor_host_rs.count() > 0:
                        for r in filter_anchor_host_rs:
                            filter_execution_arr.append(r)

            # if len(filter_execution_arr) > 0:
            #     pin_request_in_rd3mn(filter_execution_arr)

            response_data['status'] = 1
            response_data['message'] = 'History list.'
            # response_data['history_execute_request'] = list(anchor_rs)
            # response_data['filter_anchors'] = test_arr
            response_data['union'] = new_arr
            response_data['union1234'] = short_array
            # response_data['enque_anchors'] = list(enqueue_anchor_host_rs)
            # response_data['filter_hits'] = final_arr
            # response_data['Grater Then Ten Execution AnchorName Array'] = graterThenNineExecutionAnchorNameArray
            # response_data['Less Then Ten Execution AnchorName Array'] = lessThenNineExecutionAnchorNameArray
            # response_data['history'] = list(anchor_host_rs)
            response_data['selected_obj'] = filter_execution_arr
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 1
            response_data['message'] = 'History list blank.'
            response_data['history'] = []
            return JsonResponse(response_data, status=200) 
            response_data['status'] = 1
            response_data['message'] = 'History list blank.'
            response_data['history'] = []
            return JsonResponse(response_data, status=200)


def RD3MNPinCommandExecutionCornView():
    test_arr = []
    final_arr = []
    new_arr = []
    short_array = []
    request_load_limit_per_anchor = 12
    anchor_host_rs = CommendExecutionHistoryDetails.objects.filter(query_status='enqueue', anchor_name__isnull=False,
                                                                   commend_execution_history_id__query='ping')
    anchor_host_rs = anchor_host_rs.values('id', 'anchor_name', 'commend_request_payload',
                                           'user_anchor_id__anchor_id__server_url', 'commend_execution_history_id')
    anchor_host_rs = anchor_host_rs.order_by('id')
    anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-blr-anchor')
    anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-gwh-anchor')
    anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-kol-anchor')
    anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-moh-anchor')
    anchor_host_rs = anchor_host_rs.exclude(anchor_name='nats-mum-anchor')
    # anchor_host_rs = anchor_host_rs.annotate(query_count=Count('commend_execution_history_id'))
    if anchor_host_rs:
        # anchor_rs = CommendExecutionHistoryDetails.objects.filter(query_status='running', anchor_name__isnull=False)
        # anchor_rs = anchor_rs.values('anchor_name')
        # anchor_rs = anchor_rs.order_by('user_anchor_id')
        # anchor_rs = anchor_rs.exclude(anchor_name ='nats-blr-anchor')
        # anchor_rs = anchor_rs.exclude(anchor_name ='nats-gwh-anchor')
        # anchor_rs = anchor_rs.exclude(anchor_name ='nats-kol-anchor')
        # anchor_rs = anchor_rs.exclude(anchor_name ='nats-moh-anchor')
        # anchor_rs = anchor_rs.exclude(anchor_name ='nats-mum-anchor')
        # anchor_rs = anchor_rs.annotate(anchor_count=Count('user_anchor_id'))
        # if anchor_rs:
        #     for an in anchor_rs:
        #         if an['anchor_count'] <= request_load_limit_per_anchor:
        #             # test_arr.append(an['anchor_name'])
        #             test_arr.append(an)
        # if len(test_arr) > 0:
        #     # for n in anchor_host_rs:
        #     #     if n['anchor_name'] in test_arr:
        #     #         final_arr.append(n)
        #     for x in test_arr:
        #         filter_anchor_host_rs = CommendExecutionHistoryDetails.objects.filter(query_status='enqueue', anchor_name=x['anchor_name'])
        #         filter_anchor_host_rs = filter_anchor_host_rs.values('id', 'anchor_name', 'commend_request_payload', 'user_anchor_id__anchor_id__server_url', 'commend_execution_history_id')
        #         filter_anchor_host_rs = filter_anchor_host_rs.order_by('id')[:request_load_limit_per_anchor]
        #         print('&&&&&&&&&&&&& filter_anchor_host_rs &&&&&&&&&&&&&', filter_anchor_host_rs.query)
        #         if filter_anchor_host_rs:
        #             for r in filter_anchor_host_rs:
        #                 final_arr.append(r)
        # else:
        #     final_arr = list(anchor_host_rs)

        ######## Start: New Code Add Dated On 11-03-2022 ##########
        a_rs = CommendExecutionHistoryDetails.objects.filter(Q(query_status='running') | Q(query_status='enqueue'))
        a_rs = a_rs.filter(anchor_name__isnull=False, commend_execution_history_id__query='ping')
        a_rs = a_rs.values('anchor_name')
        a_rs = a_rs.order_by('user_anchor_id')
        a_rs = a_rs.exclude(anchor_name='nats-blr-anchor')
        a_rs = a_rs.exclude(anchor_name='nats-gwh-anchor')
        a_rs = a_rs.exclude(anchor_name='nats-kol-anchor')
        a_rs = a_rs.exclude(anchor_name='nats-moh-anchor')
        a_rs = a_rs.exclude(anchor_name='nats-mum-anchor')
        a_rs = a_rs.annotate(anchor_count=Count('user_anchor_id'))

        if a_rs:
            for r in a_rs:
                b_rs = CommendExecutionHistoryDetails.objects.filter(query_status='running', anchor_name__isnull=False,
                                                                     anchor_name=r['anchor_name'],
                                                                     commend_execution_history_id__query='ping')
                b_rs = b_rs.values('anchor_name')
                b_rs = b_rs.order_by('user_anchor_id')
                b_rs = b_rs.exclude(anchor_name='nats-blr-anchor')
                b_rs = b_rs.exclude(anchor_name='nats-gwh-anchor')
                b_rs = b_rs.exclude(anchor_name='nats-kol-anchor')
                b_rs = b_rs.exclude(anchor_name='nats-moh-anchor')
                b_rs = b_rs.exclude(anchor_name='nats-mum-anchor')
                b_rs = b_rs.annotate(anchor_count=Count('user_anchor_id'))
                if b_rs:
                    for b in b_rs:
                        new_arr.append(b)
                else:
                    # print('&&&&&&&&&&&&&&&& ANCHOR NAME IS &&&&&&&&&&&&&&&&&', r['anchor_name'])
                    # print('&&&&&&&&&&&&&&&& ANCHOR COUNT IS &&&&&&&&&&&&&&&&&', r['anchor_count'])
                    new_arr.append({'anchor_name': r['anchor_name'], 'anchor_count': 0})

        if len(new_arr) > 0:
            for na in new_arr:
                # print('&&&&&&&&&&&&&&&& ANCHOR NAME IS &&&&&&&&&&&&&&&&&', na['anchor_name'])
                # print('&&&&&&&&&&&&&&&& ANCHOR COUNT IS &&&&&&&&&&&&&&&&&', na['anchor_count'])
                if na['anchor_count'] <= request_load_limit_per_anchor:
                    short_array.append(na)

        if len(short_array) > 0:
            query_limit = 0
            for x in short_array:
                query_limit = int(request_load_limit_per_anchor) - int(x['anchor_count'])
                filter_anchor_host_rs = CommendExecutionHistoryDetails.objects.filter(query_status='enqueue',
                                                                                      anchor_name=x['anchor_name'],
                                                                                      commend_execution_history_id__query='ping')
                filter_anchor_host_rs = filter_anchor_host_rs.values('id', 'anchor_name', 'commend_request_payload',
                                                                     'user_anchor_id__anchor_id__server_url',
                                                                     'commend_execution_history_id',
                                                                     'query_execution_interval_unit',
                                                                     'query_execution_interval_time')
                filter_anchor_host_rs = filter_anchor_host_rs.order_by('id')[:query_limit]
                # print('&&&&&&&&&&&&& filter_anchor_host_rs &&&&&&&&&&&&&', filter_anchor_host_rs.count())
                if filter_anchor_host_rs.count() > 0:
                    for r in filter_anchor_host_rs:
                        final_arr.append(r)
        ######## End: New Code Add Dated On 11-03-2022 ##########

        ## Execute Pin Request In RD3MN Server
        if len(final_arr) > 0:
            pin_request_in_rd3mn(final_arr)

# def filter_command_history_query(filter_param: str):
#     terms = [q.strip() for q in query_param.split(',') if q.strip()]
#     print("param......................................", terms)
#
#     # Initialize an empty Q filter
#     q_filter = Q()
#
#     # Loop through the terms and create an OR condition for each term
#     for term in terms:
#         q_filter |= Q(query__icontains=term)
#
#     # Apply the filter to the queryset
#     qs = qs.filter(q_filter)