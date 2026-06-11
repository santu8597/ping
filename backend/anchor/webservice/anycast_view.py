from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sessions.models import Session
from django.utils.crypto import get_random_string
from django.conf import settings
from collections import defaultdict
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
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from datetime import datetime, timedelta,date
from datetime import datetime as dt, time
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import django.db.models
from django.db.models import Max, Count, Sum, Avg
from django.db.models import Q, F
from backend.anchor.models import *
from backend.users.models import *
from backend.anchor.serializers import *
from backend.users.serializers import *
import json
from django.utils import timezone
import requests
import os
import base64
import geocoder
from django.db.models.signals import post_save
from django.dispatch import receiver
from backend.anchor.models import ServeMeasurementHistory
import threading
import random
from django.db.models.functions import TruncYear, TruncMonth, TruncWeek, TruncQuarter, TruncDate, TruncDay, TruncHour, TruncMinute, TruncSecond
from django.db.models.functions import ExtractMonth
from datetime import datetime, timedelta
from datetime import date
import datetime
from functools import reduce

from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from config_env import CONFIG

## For IPINFO
# from django.shortcuts import render
# from django.http import HttpResponse 
# from django.conf import settings
import ipinfo
from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry

from backend.utils.helpers import get_cache, set_cache


DEFAULT_BATCH_SIZE = 1000
DEFAULT_MAX_WORKERS = 20
DEFAULT_TIMEOUT = 10
API_KEY = "996b6ecf6cdd0df6aa5ffeffaca6983b"
LOG_PROGRESS_EVERY = 100

def mesurmentResult(obj):
    # print('========================', obj)
    newSet = []
    ietrval = str('300s')
    for his in obj:
        dataSet = {}
        query_payload = his['commend_request_payload']
        query_id = str(his['commend_query_id'])
        # print('HOST', query_payload["hosts"])
        host = ''.join(query_payload["hosts"])
        dataSet['anchor_name'] = his['anchor_name']
        dataSet['register_location'] = his['register_location']
        dataSet['latitude'] = his['latitude']
        dataSet['longitude'] = his['longitude']
        dataSet['aiori_anchor_id'] = his['aiori_anchor_id']
        dataSet[host] = []
        resultSet = {
            "time": timezone.now(),
            "destination": host,
            "rtt_avg": 0
        }
        query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id + "' AND time < now() group by destination, time(" + ietrval + ")"
        # query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id + "' AND time < now() group by destination, time(" + ietrval + ")"
        # print('$$$$$$$$$$$$$$$$$$', query)
        result = requests.get(query)
        if result.status_code == 200:
            json_result = result.json()
            msg = 'Data set is ready.'
            for val in json_result['results']:
                # print(val)
                if "series" in val:
                    for ser in val['series']:
                        if "values" in ser:
                            for value in ser['values']:
                                res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                dataSet[host].append(res)
                        else:
                            dataSet[host].append(resultSet)
                            msg = 'Values key is not present in your data set.'
                else:
                    dataSet[host].append(resultSet)
                    msg = 'Series key is not present in your data set.'
            print(1)
            newSet.append(dataSet)
        else:
            newSet.append(dataSet)
    # response_data['status'] = 1
    # response_data['message'] = msg
    # response_data['data'] = dataSet
    # return JsonResponse(response_data, status=200)
    return newSet

def RegularMesurmentResult(obj):
    newSet = []
    updated_dataset = []
    for his in obj:
        # print('========================', his)
        dataSet = {}

        query_id = str(his['commend_query_id'])
        anchor_location = his["vartual_anchor_location"]
        db_url = his["anchor_id__db_url"]
        storage_db_name = his["anchor_id__storage_db"]
        #print('$$$$$$$$$$$$$$$$$$ db_url', db_url)
        #print('$$$$$$$$$$$$$$$$$$ storage_db_name', storage_db_name)
        dataSet[anchor_location] = []
        resultSet = {
            "time": timezone.now(),
            "rtt_avg": 0,
            "rtt_max": 0,
            "rtt_min": 0
        }
        # resultSet.update({'history_id': his["serve_measurement_history_id"], 'history_details_id': his["id"]})
        # updated_dataset.append(resultSet)
        # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT * FROM ping WHERE id='" + query_id
        # query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT rtt_avg, rtt_max, rtt_min FROM ping WHERE id='" + query_id + "'"
        query = str(db_url) + "/query?pretty=true&db=" + str(storage_db_name) + "&q=SELECT rtt_avg, rtt_max, rtt_min, protocol FROM ping WHERE id='" + query_id + "'"
        #print('$$$$$$$$$$$$$$$$$$', query)
        result = requests.get(query)
        #print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', result.status_code)
        if result.status_code == 200:
            json_result = result.json()
            msg = 'Data set is ready.'
            for val in json_result['results']:
                # print(val)
                if "series" in val:
                    for ser in val['series']:
                        if "values" in ser:
                            for value in ser['values']:
                                res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))}
                                resultSet = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))}
                                resultSet.update({'history_id': his["serve_measurement_history_id"], 'history_details_id': his["id"]})
                                dataSet[anchor_location].append(res)
                                updated_dataset.append(resultSet)
                        else:
                            dataSet[anchor_location].append(resultSet)
                            updated_dataset.append({'history_id': his["serve_measurement_history_id"], 'history_details_id': his["id"], 'time': timezone.now(), 'rtt_avg': 0, 'rtt_max': 0, 'rtt_min': 0, 'protocol': ''})
                            msg = 'Values key is not present in your data set.'
                else:
                    dataSet[anchor_location].append(resultSet)
                    updated_dataset.append({'history_id': his["serve_measurement_history_id"], 'history_details_id': his["id"], 'time': timezone.now(), 'rtt_avg': 0, 'rtt_max': 0, 'rtt_min': 0, 'protocol': ''})
                    msg = 'Series key is not present in your data set.'
            print(1)
            newSet.append(dataSet)
        else:
            resultSet.update({'history_id': his["serve_measurement_history_id"], 'history_details_id': his["id"]})
            updated_dataset.append(resultSet)
            newSet.append(dataSet)
    InsertLatency(updated_dataset)
    return newSet

def InsertLatency(obj):
    #print('&&&&&&&&&&&&&&&&&&&&&&&&& InsertLatency &&&&&&&&&&&&&&&&&&&&&&&&', obj)
    history_latency_status = 'running'
    for val in obj:
        # print('val', val)
        if val['rtt_avg'] != 0:
            print('True', val['rtt_avg'])
            history_latency_status = 'success'
            mesurObj = ServeMeasurementHistoryDetails.objects.filter(id=val['history_details_id']).update(rtt_avg=val['rtt_avg'], rtt_max=val['rtt_max'], rtt_min=val['rtt_min'], time=val['time'], protocol=val['protocol'])
            rs = ServeMeasurementHistory.objects.filter(id=val['history_id']).update(latency_status=history_latency_status)
        else:
            print('False', val['rtt_avg'])

class LocationWiseMeasurementView(APIView):
    def get(self,request):
        response_data = {}
        # rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active", anchor_id__is_online=True)
        # rs = rs.order_by('-id')
        rs = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, status='active', location_register_status='registered')
        rs = rs.filter(anchor_id__is_online=True)
        rs = rs.order_by('-anchor_id')
        rs = rs.values('id', 'anchor_id__anchor_name', 'location', 'latitude', 'longitude', 'aiori_anchor_id')
        rs = rs.distinct('anchor_id')
        # print(rs)
        # response_data['status'] = 0
        # response_data['message'] = 'Measurement not found.'
        # response_data['data'] = []
        # return JsonResponse(response_data, status=200)
        if rs:
            sets = []
            for anchor_id in rs:
                Obj = CommendExecutionHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, check_points_status='success', user_anchor_id=anchor_id['id']).values('id', 'commend_query_id', 'user_anchor_id', 'commend_request_payload', 'commend_execution_history__query_execution_end_date').last()
                if Obj:
                    # print()
                    Obj['anchor_name'] = anchor_id['anchor_id__anchor_name']
                    Obj['register_location'] = anchor_id['location']
                    Obj['latitude'] = anchor_id['latitude']
                    Obj['longitude'] = anchor_id['longitude']
                    Obj['aiori_anchor_id'] = anchor_id['aiori_anchor_id']
                    sets.append(Obj)
                    # print('**********************', Obj)
            if sets:
                result = mesurmentResult(sets)
                # print(result)
                response_data['status'] = 1
                response_data['message'] = 'Measurement found.'
                response_data['data'] = result
            else:
                response_data['status'] = 0
                response_data['message'] = 'Measurement not found.'
                response_data['data'] = []
        else:  
            response_data['status'] = 0
            response_data['message'] = 'Measurement not found.'
            response_data['data'] = []
        return JsonResponse(response_data, status=200)

    def post(self,request):
        response_data = {}
        requestData = request.data
        rs = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, status='active', location_register_status='registered', aiori_anchor_id=requestData['anchor_id'])
        rs = rs.filter(anchor_id__is_online=True)
        rs = rs.order_by('-anchor_id')
        rs = rs.values('id', 'anchor_id__anchor_name', 'location', 'latitude', 'longitude', 'aiori_anchor_id')
        rs = rs.distinct('anchor_id')
        if rs:
            sets = []
            for anchor_id in rs:
                # print('anchor_id', anchor_id['id'])
                Obj = CommendExecutionHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, check_points_status='success', user_anchor_id=anchor_id['id']).values('id', 'commend_query_id', 'user_anchor_id', 'commend_request_payload').last()
                if Obj:
                    Obj['anchor_name'] = anchor_id['anchor_id__anchor_name']
                    Obj['register_location'] = anchor_id['location']
                    Obj['latitude'] = anchor_id['latitude']
                    Obj['longitude'] = anchor_id['longitude']
                    Obj['aiori_anchor_id'] = anchor_id['aiori_anchor_id']
                    sets.append(Obj)
                    #print('**********************', Obj)
            if sets:
                # print('**********************', sets)
                result = mesurmentResult(sets)
                # print(result)
                response_data['status'] = 1
                response_data['message'] = 'Measurement found.'
                response_data['data'] = result
            else:
                response_data['status'] = 0
                response_data['message'] = 'Measurement not found.'
                response_data['data'] = []
        else:  
            response_data['status'] = 0
            response_data['message'] = 'Measurement not found.'
            response_data['data'] = []
        return JsonResponse(response_data, status=200)


def get_anchor_location(anchor_name):
    anchor_location = 'kolkata'
    if anchor_name == "nats-gwh-anchor":
        anchor_location = 'Guwahati'
    if anchor_name == "nats-kol-anchor":
        anchor_location = 'Kolkata'
    if anchor_name == "nats-moh-anchor":
        anchor_location = 'Mohali'
    if anchor_name == "nats-blr-anchor":
        anchor_location = 'Bengaluru'
    if anchor_name == "nats-mum-anchor":
        anchor_location = 'Mumbai'
    return anchor_location



def executed_measurement(serve_mesur_id, serve_location, host):
    print('executed_measurement', serve_mesur_id)
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active", location_register_status="registered", anchor_id__is_online=True)
    rs = rs.filter(Q(anchor_id__anchor_name='nats-blr-anchor') | Q(anchor_id__anchor_name='nats-mum-anchor') | Q(anchor_id__anchor_name='nats-kol-anchor') | Q(anchor_id__anchor_name='nats-gwh-anchor') | Q(anchor_id__anchor_name='nats-moh-anchor'))
    rs = rs.values('id', 'anchor_id__anchor_name', 'lease_id', 'aiori_anchor_id', 'anchor_id__server_url', 'anchor_id')
    rs = rs.order_by('-id')
    # print(rs.query)
    if rs:
        for anchor in rs:
            # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& ANCHOR SERVER URL &&&&&&&&&&&&&&&&&&&&&&&&&&&&&7', anchor['anchor_id__server_url'])
            # anchor_obj = Anchor.objects.filter(id=anchor.anchor_id).first()
            # url = str(settings.AIORI_ANCHOR_HOST) + str(settings.AIORI_ANCHOR_URL) + "ping/?lease_id=" + anchor['lease_id']
            url = str(anchor['anchor_id__server_url']) + "ping/?lease_id=" + anchor['lease_id']
            data = {
                    "cmd_value": "ping",
                    "cmd_type": "regular",
                    "run_count": "3",
                    "region": serve_location.lower(),
                    "hosts": [host],
                    "anchors": [anchor['aiori_anchor_id']]
                    }   
            # params = {'sessionKey': '9ebbd0b25760557393a43064a92bae539d962103', 'format': 'xml', 'platformId': 1}
            #print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&7', anchor['anchor_id'])
            # print(data)
            vartual_anchor_location = get_anchor_location(anchor['anchor_id__anchor_name'])
            obj = ServeMeasurementHistoryDetails.objects.create(
                serve_measurement_history_id =serve_mesur_id,
                commend_request_payload = data,
                vartual_anchor_location = vartual_anchor_location,
                anchor_id = anchor['anchor_id'],
                created_date = timezone.now(),
                modified_date = timezone.now(),
            )
            result = requests.post(url, json=data, headers=set_headers)
            if result.status_code == 200:
                json_result = result.json()
                obj = ServeMeasurementHistoryDetails.objects.filter(id=obj.id).update(commend_query_id=json_result['id'])
                print(json_result['id'])
            else:
                print(result.status_code)
                result


def add_serve_measurement(obj_id, address, country, state, city, postal, latitude, longitude, serve_location, host):
    #print('add_serve_measurement', obj_id)
    serve_measurement_id = get_random_string(length=21)
    #print('add_serve_measurement', serve_measurement_id)
    obj = ServeMeasurementHistory.objects.create(
        serve_ip_details_id=obj_id,
        serve_measurement_id=serve_measurement_id,
        serve_location=serve_location,
        commend_request_payload='',
        address= address,
        country= country,
        state= state,
        city= city,
        postal= postal,
        latitude= latitude,
        longitude= longitude,
        created_date=timezone.now(),
        modified_date=timezone.now(),
    )
    executed_measurement(obj.id, serve_location, host)
    return serve_measurement_id

# @receiver(post_save, sender=ServeMeasurementHistory)
# def executed_measurement(sender, **kwargs):
#     print(sender)
#     print(kwargs)
    # i = 0
    # count = 10000
    # while i < count:
    #     i += 1
        # print('post save callback', i)


def get_ip_details(ip_address=None):
	ipinfo_token = getattr(settings, "IPINFO_TOKEN", None)
	ipinfo_settings = getattr(settings, "IPINFO_SETTINGS", {})
	ip_data = ipinfo.getHandler(ipinfo_token, **ipinfo_settings)
	ip_data = ip_data.getDetails(ip_address).all
	return ip_data

class MeasurementServeView(APIView):
    def get(self,request, measurementid):
        #print('measurementid', measurementid)
        response_data = {}
        if measurementid:
            rs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, serve_measurement_id=measurementid).first()
            if rs:
                #print('******************************', rs.id)
                mesurObj = ServeMeasurementHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, serve_measurement_history=rs.id)
                anchor_return_measurement = 0
                if rs.latency_status == 'running':
                    mesurObj = mesurObj.values('id', 'serve_measurement_history_id', 'commend_query_id', 'vartual_anchor_location', 'anchor_id__db_url', 'anchor_id__storage_db')
                    mesurObj = mesurObj.order_by('id')
                    result = RegularMesurmentResult(mesurObj)
                else:
                    result = []
                    mesurObj = mesurObj.values('id', 'vartual_anchor_location', 'rtt_avg', 'rtt_max', 'rtt_min', 'time', 'protocol')
                    mesurObj = mesurObj.order_by('id')
                    anchor_return_measurement = 1
                    if mesurObj:
                        for obj in mesurObj:
                            dataSet = {}
                            location = obj['vartual_anchor_location']
                            dataSet[location] = []
                            dataSet[location].append({'rtt_avg':obj['rtt_avg'], 'rtt_max':obj['rtt_max'], 'rtt_min':obj['rtt_min'], 'time':obj['time'], 'protocol':obj['protocol']})
                            result.append(dataSet)
                # print(mesurObj.query)
                response_data['status'] = 1
                response_data['message'] = 'Serve measurement found.'
                response_data['anchor_return'] = anchor_return_measurement
                response_data['mesurements'] = result
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'Serve measurement id is not in our database.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:  
            response_data['status'] = 0
            response_data['message'] = 'Serve measurement id is required.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        response_data = {}
        requestData = request.data
        ip = requestData['ip']
        # print('&&&&&&&&&&&&&&&&&&& Serve Measurement &&&&&&&&&&&&&&&&&&&&&&', requestData)
        # print('&&&&&&&&&&&&&&&&&&& Serve Measurement IP &&&&&&&&&&&&&&&&&&&&&&', requestData['ip'])
        # g = geocoder.ip(requestData['ip'], token=CONFIG.IPINFO_TOKEN_NEW)

        g = ipinfo_lookup(ip)
        # geo = map_ipinfo(g.json())
        geo = map_ipinfo(g.get("data"))
        print("sending ip----", ip)
        # print("geocoder data----", g.json())
        print("geocoder data----", g)
        print("geo data----", geo)
        if g["status_code"] == 200:
            # print(g.json())
            print("Success data==", g)
            pi_details = {}
            rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, ip=ip, serve_location=requestData['serve']).first()
            if rs:
                counter = rs.request_counter + 1
                #print(rs.request_counter)
                obj = ServeIpDetails.objects.filter(ip=ip).update(request_counter=counter, modified_date = timezone.now())
                result = add_serve_measurement(rs.id, rs.address, rs.country, rs.state, rs.city, rs.postal, rs.latitude, rs.longitude, requestData['serve'], requestData['ip'])
                pi_details = IpDetailsSerializer(rs, many=False).data
                pi_details['measurement_id'] = result
                pi_details['serve_ip_details_id'] = rs.id
                #print('UPDATE OBJ ID', rs.id)
            else:
                #print('&&&&&&&&&&&&&&&&&', rs)
                # obj = ServeIpDetails.objects.create(
                #     serve_location = requestData['serve'],
                #     address = g.address,
                #     country = g.country,
                #     state = g.state,
                #     city = g.city,
                #     postal = g.postal,
                #     latitude = g.lat,
                #     longitude = g.lng,
                #     ip = requestData['ip'],
                #     org = g.org,
                #     created_date = timezone.now(),
                #     modified_date = timezone.now(),
                # )
                obj = ServeIpDetails.objects.create(
                    serve_location=requestData["serve"],
                    address=geo["address"],
                    country=geo["country"],
                    state=geo["state"],
                    city=geo["city"],
                    postal=geo["postal"],
                    latitude=geo["latitude"],
                    longitude=geo["longitude"],
                    ip=requestData["ip"],
                    org=geo["org"],
                    created_date=timezone.now(),
                    modified_date=timezone.now(),
                )
                print("obj data---", obj)
                result = add_serve_measurement(obj.id, obj.address, obj.country, obj.state, obj.city, obj.postal,
                                               obj.latitude, obj.longitude, requestData['serve'], requestData['ip'])
                pi_details = IpDetailsSerializer(obj, many=False).data
                pi_details['measurement_id'] = result
                pi_details['serve_ip_details_id'] = obj.id
                # print('INSERT OBJ ID', obj.id)
            response_data['status'] = 1
            response_data['message'] = 'Measurement execute successfully.'
            response_data['data'] = pi_details
            return JsonResponse(response_data, status=200)
        else:
            pi_details = {}
            rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, ip=requestData['ip'],
                                               serve_location=requestData['serve']).first()
            if rs:
                counter = rs.request_counter + 1
                #print(rs.request_counter)
                obj = ServeIpDetails.objects.filter(ip=requestData['ip']).update(request_counter=counter)
                result = add_serve_measurement(rs.id, requestData['serve'], requestData['ip'])
                pi_details = IpDetailsSerializer(rs, many=False).data
                pi_details['measurement_id'] = result
                #print('UPDATE OBJ ID', rs.id)
            else:
                #print('&&&&&&&&&&&&&&&&&', rs)
                obj = ServeIpDetails.objects.create(
                    serve_location = requestData['serve'],
                    ip = requestData['ip'],
                    created_date = timezone.now(),
                    modified_date = timezone.now(),
                )
                result = add_serve_measurement(obj.id, requestData['serve'], requestData['ip'])
                pi_details = IpDetailsSerializer(obj, many=False).data
                pi_details['measurement_id'] = result
            response_data['status'] = 1
            response_data['message'] = 'Measurement execute successfully.'
            response_data['data'] = pi_details
            return JsonResponse(response_data, status=200)

class MeasurementServeDetailsView(APIView):
    def get(self,request):
        response_data = {}
        # metrics =  {
        #     'total': Count('id'),
        #     'count': Sum('request_counter'),
        #     'request_count_avg': Avg('request_counter')
        # }
        # rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False).values('serve_location').annotate(**metrics)

        rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('serve_location').values('serve_location').annotate(count=Sum('request_counter'))
        if rs:
            label = []
            serise = []
            data = []
            for n in rs:
                label.append(n['serve_location'])
                serise.append(n['count'])
            data.append({'data': serise, 'label': label})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['serve'] = data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        from datetime import date
        import datetime
        response_data = {}
        requestData = request.data
        if requestData:
            print('&&&&&&&&&&&&&&&&&&&&&', requestData)
        else:
            some_date = date.today()
            three_months = datetime.timedelta(6*365/12)
            #print ('Three Month Befour Feom Today', some_date - three_months)

            today = date.today()
            # YY-mm-dd
            # d1 = today.strftime("%d/%m/%Y")
            d1 = today.strftime("%Y-%m-%d")
            #print("d1 =", d1)
            #print('&&&&&&&&&&&&&&&&&&&&&', 'NO DATA')
        rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('serve_location').values('serve_location').annotate(count=Sum('request_counter'))
        if rs:
            label = []
            serise = []
            data = []
            for n in rs:
                label.append(n['serve_location'])
                serise.append(n['count'])
            data.append({'data': serise, 'label': label})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            # response_data['serve'] = data
            response_data['serve'] = list(rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class MeasurementServeDetailsPieView(APIView):
    def get(self,request):
        response_data = {}
        rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False).order_by('serve_location').values('serve_location').annotate(count=Sum('request_counter'))
        if rs:
            total_hites = 0
            label = []
            serise = []
            data = []
            for n in rs:
                total_hites = total_hites + n['count']
            for n in rs:
                avg = 0
                label.append(n['serve_location'])
                avg = 100 * (n['count'] / total_hites)
                serise.append(avg)
            data.append({'data': serise, 'label': label})
            #print(total_hites)
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['data'] = data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class ServeMapView(APIView):
    # def get(self,request):
    #     response_data = {}
    #     data = []
    #     latlong = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, city__isnull=False, latitude__isnull=False, longitude__isnull=False).values('latitude', 'longitude', 'address', 'postal', 'org', 'request_counter').distinct('latitude', 'longitude')
    #
    #     rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, city__isnull=False, latitude__isnull=False, longitude__isnull=False).order_by('city').values('city', 'latitude', 'longitude', 'id').annotate(count=Sum('request_counter'))
    #     # rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, city__isnull=False, latitude__isnull=False, longitude__isnull=False).order_by('city').values('city').annotate(count=Sum('request_counter'))
    #
    #     mesurHisDtlqs = ServeMeasurementHistoryDetails.objects.filter(is_deleted=False, is_blocked=False).exclude(rtt_avg =0).order_by('serve_measurement_history_id').values_list('serve_measurement_history_id')
    #     # print('&&&&&&&&&&&&&&&&&&', mesurHisDtlqs.query)
    #     city = {}
    #     if mesurHisDtlqs:
    #         mesurHisqs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, id__in=mesurHisDtlqs).order_by('serve_location').values_list('serve_ip_details_id')
    #         if mesurHisqs:
    #             rs1 = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, city__isnull=False, latitude__isnull=False, longitude__isnull=False, id__in=mesurHisqs).order_by('city').values('city', 'latitude', 'longitude', 'id').annotate(count=Sum('request_counter'))
    #             #print('&&&&&&&&&444444444444444444&&&&&&&&&', rs1.query)
    #             if mesurHisqs:
    #                 for n in rs1:
    #                     hit_count =  n['count']
    #                     keys = city.keys()
    #                     if n['city'] in city:
    #                         for key in city:
    #                             # print(city)
    #                             if key == n['city']:
    #                                 # print('KEY',key)
    #                                 # print('Ncity', n['city'])
    #                                 city[key].append({'lat': float(n['latitude']), 'lng': float(n['longitude']), 'count':int(hit_count)})
    #                     else:
    #                         city[n['city']] = []
    #                         city[n['city']].append({'lat': float(n['latitude']), 'lng': float(n['longitude']), 'count':int(hit_count)})
    #
    #     if rs:
    #         # city = {}
    #         # for n in rs:
    #         #     hit_count =  n['count']
    #         #     keys = city.keys()
    #         #     if n['city'] in city:
    #         #         for key in city:
    #         #             # print(city)
    #         #             if key == n['city']:
    #         #                 # print('KEY',key)
    #         #                 # print('Ncity', n['city'])
    #         #                 city[key].append({'lat': float(n['latitude']), 'lng': float(n['longitude']), 'count':int(hit_count)})
    #         #     else:
    #         #         city[n['city']] = []
    #         #         city[n['city']].append({'lat': float(n['latitude']), 'lng': float(n['longitude']), 'count':int(hit_count)})
    #         data.append({'circledata': list(rs), 'markerdata':list(latlong), 'citis':city, 'cities': list(rs1)})
    #         # data.append({'circledata': list(rs), 'markerdata':list(latlong)})
    #         response_data['status'] = 1
    #         response_data['message'] = 'Serve location found.'
    #         # response_data['latlong'] = list(latlong)
    #         response_data['data'] = data
    #         return JsonResponse(response_data, status=200)
    #     else:
    #         response_data['status'] = 0
    #         response_data['message'] = 'No record found in our database.'
    #         response_data['data'] = []
    #         return JsonResponse(response_data, status=200)
    def get(self, request):
        # Use your custom Redis cache alias (change if you use different alias)
        cache_alias = "default"
        cache_key = "serve_map_data"

        response_data = get_cache(cache_alias, cache_key)

        if response_data is None:
            response_data = {}
            try:
                markerdata = ServeIpDetails.objects.filter(
                    is_deleted=False, is_blocked=False,
                    serve_location__isnull=False,
                    city__isnull=False,
                    latitude__isnull=False,
                    longitude__isnull=False
                ).values('latitude', 'longitude', 'address', 'postal', 'org').distinct('latitude', 'longitude')

                circledata = ServeIpDetails.objects.filter(
                    is_deleted=False, is_blocked=False,
                    serve_location__isnull=False,
                    city__isnull=False,
                    latitude__isnull=False,
                    longitude__isnull=False
                ).values('city', 'latitude', 'longitude').annotate(count=Sum('request_counter'))

                mesurHisDtlqs = ServeMeasurementHistoryDetails.objects.filter(
                    is_deleted=False, is_blocked=False
                ).exclude(rtt_avg=0).values_list('serve_measurement_history_id', flat=True)

                rs1 = []
                city_map = defaultdict(list)

                if mesurHisDtlqs:
                    mesurHisqs = ServeMeasurementHistory.objects.filter(
                        is_deleted=False, is_blocked=False,
                        id__in=mesurHisDtlqs
                    ).values_list('serve_ip_details_id', flat=True)

                    rs1 = ServeIpDetails.objects.filter(
                        is_deleted=False, is_blocked=False,
                        id__in=mesurHisqs,
                        serve_location__isnull=False,
                        city__isnull=False,
                        latitude__isnull=False,
                        longitude__isnull=False
                    ).values('city', 'latitude', 'longitude').annotate(count=Sum('request_counter'))

                    for item in rs1:
                        city_map[item['city']].append({
                            'lat': float(item['latitude']),
                            'lng': float(item['longitude']),
                            'count': int(item['count'])
                        })

                response_data = {
                    'status': 1,
                    'message': 'Serve location found.',
                    'data': [{
                        'markerdata': list(markerdata),
                        'circledata': list(circledata),
                        'cities': list(rs1),
                        'citis': city_map,
                    }]
                }

                # Use your helper to cache it
                set_cache(cache_alias, cache_key, response_data, timeout=300)

            except Exception as e:
                response_data = {
                    'status': 0,
                    'message': f'Error fetching data: {str(e)}',
                    'data': []
                }

        return JsonResponse(response_data, status=200)
    def post(self,request):
        response_data = {}
        requestData = request.data
        print('&&&&&&&&&&&&&&', requestData)
        data = []
        latlong = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, city__isnull=False, latitude__isnull=False, longitude__isnull=False, serve_location__in=requestData['serve_location']).values('latitude', 'longitude', 'address', 'postal', 'org', 'request_counter')
        print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', latlong.query)
        rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, city__isnull=False, latitude__isnull=False, longitude__isnull=False, serve_location__in=requestData['serve_location']).order_by('city').values('city', 'latitude', 'longitude').annotate(count=Sum('request_counter'))
        # print(rs.query)
        if rs:
            city = {}
            for n in rs:
                hit_count =  n['count']
                # if n['city'] in city:
                #     for key in city:
                #         # print(city[key]['count'])
                #         if key == n['city']:
                #             hit_count = city[key]['count'] + n['count']
                # else:
                #     hit_count = n['count']
                city[n['city']] = {'center':{ 'lat': float(n['latitude']), 'lng': float(n['longitude']) }, 'count':int(hit_count)}
            data.append({'circledata': list(rs), 'markerdata':list(latlong)})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            # response_data['latlong'] = list(latlong)
            response_data['data'] = data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class ServeLatencyByCityView(APIView):
    def get(self,request, city):
        from django.db.models import Avg
        s = city.replace('.', '=')
        # then base64decode
        # print('&&&&&&&&&&&&&&&&&&&& ENCODE BASE 64 &&&&&&&&&&&&&&&&&', base64.b64decode(s).decode('utf-8'))
        city_name = base64.b64decode(s).decode('utf-8')
        response_data = {}
        data = []
        # rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, latitude__isnull=False, longitude__isnull=False, city__istartswith=city_name).values_list('serve_ip_details_id', flat=True)
        rs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, serve_ip_details_id__serve_location__isnull=False, serve_ip_details_id__latitude__isnull=False, serve_ip_details_id__longitude__isnull=False, serve_ip_details_id__city__isnull=False,  serve_ip_details_id__city__contains=city_name).values_list('id', flat=True)
        #print('&&&&&&&&&&&&&&&&&&&& ServeMeasurementHistory &&&&&&&&&&&&&&&&&', rs.query)
        if rs:
            qs = ServeMeasurementHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, serve_measurement_history_id__in=rs).\
            exclude(rtt_avg =0).\
            extra({'created_day':"date(created_date)"}).\
            values('vartual_anchor_location').\
            annotate(avg_latency=Avg('rtt_avg'))
            # print('&&&&&&&&&&&&&&&&&&', qs.query)
            response_data['status'] = 1
            response_data['message'] = 'Latency found.'
            response_data['data'] = list(qs)
            # response_data['ids'] = list(rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        response_data = {}
        data = []
        rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, latitude__isnull=False, longitude__isnull=False, city__istartswith=city_name).values_list('serve_ip_details_id', flat=True)
        if rs:
            qs = ServeMeasurementHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, serve_measurement_history__in=rs).\
            exclude(rtt_avg =0).\
            extra({'created_day':"date(created_date)"}).\
            values('vartual_anchor_location').\
            annotate(avg_latency=Avg('rtt_avg'))
            # print('&&&&&&&&&&&&&&&&&&', qs.query)
            response_data['status'] = 1
            response_data['message'] = 'Latency found.'
            response_data['data'] = list(qs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)
'''
def latency_check_measurement(latency_check_history_id, host, rs_data=None):
    bulk_insert_record_set = []
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    print('executed_measurement', latency_check_history_id)
    # rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, location__isnull=False, status="active", location_register_status="registered", anchor_id__is_online=True)
    # rs = rs.values('id', 'anchor_id', 'lease_id', 'aiori_anchor_id', 'location', 'user_id', 'anchor_id__server_url')
    # rs = rs.order_by('-id')
    if rs_data:
        rs = rs_data
    else:
        rs = get_active_measurement_anchors_data()
    # print(rs.query)
    if rs:
        for anchor in rs:
            # anchor_obj = Anchor.objects.filter(id=anchor.anchor_id).first()
            #print('######## Server URL #########', anchor['anchor_id__server_url'])
            # url = str(settings.AIORI_ANCHOR_HOST) + str(settings.AIORI_ANCHOR_URL) + "ping/?lease_id=" + anchor['lease_id']
            url = str(anchor['anchor_id__server_url']) + "ping/?lease_id=" + anchor['lease_id']
            # print('&&&&&&&&&&&&&&', url)
            data = {
                    "cmd_value": "ping",
                    "cmd_type": "regular",
                    "run_count": "3",
                    "region": anchor['location'].lower(),
                    "hosts": [host],
                    "anchors": [anchor['aiori_anchor_id']]
                    }   
            #print('&&&&&------&&&&&&&', data)
            #print('&&&&&---Anchor Name---&&&&&&&', anchor['location'].lower())
            # obj = LatencyCheckHistoryDetails.objects.create(
            #     latency_check_history_id=latency_check_history_id,
            #     anchor_id=anchor['anchor_id'],
            #     user_anchor_id=anchor['id'],
            #     anchor_user_id=anchor['user_id'],
            #     commend_request_payload= data,
            #     register_anchor_location = anchor['location'].lower(),
            #     latency_check_domain_name = host,
            #     created_date=timezone.now(),
            #     modified_date=timezone.now(),
            # )
            result = requests.post(url, json=data, headers=set_headers)
            # print('&&&&&&&&&&&&&&  json_result  &&&&&&&&&&&&&&&&&&&&&&&&&',result.json())
            if result.status_code == 200:
                json_result = result.json()
                # print('&&&&&&&&&&&&&&  json_result  &&&&&&&&&&&&&&&&&&&&&&&&&',json_result)
                # obj = LatencyCheckHistoryDetails.objects.filter(id=obj.id).update(commend_query_id=json_result['id'])
                ########### Create Record Set #########
                bulk_insert_record_set.append(LatencyCheckHistoryDetails(
                latency_check_history_id=latency_check_history_id,
                anchor_id=anchor['anchor_id'],
                user_anchor_id=anchor['id'],
                anchor_user_id=anchor['user_id'],
                commend_request_payload= data,
                register_anchor_location = anchor['location'].lower(),
                latency_check_domain_name = host,
                commend_query_id=json_result['id'],
                created_date=timezone.now(),
                modified_date=timezone.now(),
            ))
                print(json_result['id'])
            else:
                print(result.status_code)
                result
                bulk_insert_record_set.append(LatencyCheckHistoryDetails(
                latency_check_history_id=latency_check_history_id,
                anchor_id=anchor['anchor_id'],
                user_anchor_id=anchor['id'],
                anchor_user_id=anchor['user_id'],
                commend_request_payload= data,
                register_anchor_location = anchor['location'].lower(),
                latency_check_domain_name = host,
                commend_query_id='',
                created_date=timezone.now(),
                modified_date=timezone.now(),
            ))
        print('###################### bulk_insert_record_set #################', bulk_insert_record_set)
        msg = LatencyCheckHistoryDetails.objects.bulk_create(bulk_insert_record_set)
'''
def latency_check_measurement(latency_check_history_id, host, rs_data=None):
    set_headers = {
        "content-type": "application/json",
        "apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"
    }

    print("executed_measurement", latency_check_history_id)

    rs = rs_data if rs_data else get_active_measurement_anchors_data()
    if not rs:
        return

    now = timezone.now()
    bulk_insert_record_set = []

    def process_anchor(anchor):
        server_url = anchor["anchor_id__server_url"]
        lease_id = anchor["lease_id"]
        location = anchor["location"].lower()
        aiori_anchor_id = anchor["aiori_anchor_id"]

        url = f"{server_url}ping/?lease_id={lease_id}"

        data = {
            "cmd_value": "ping",
            "cmd_type": "regular",
            "run_count": "3",
            "region": location,
            "hosts": [host],
            "anchors": [aiori_anchor_id],
        }

        commend_query_id = ""

        try:
            result = requests.post(url, json=data, headers=set_headers, timeout=20)

            if result.status_code == 200:
                json_result = result.json()
                commend_query_id = json_result.get("id", "")
                print(commend_query_id)
            else:
                print(result.status_code)

        except Exception as e:
            print("Request failed:", e)

        return LatencyCheckHistoryDetails(
            latency_check_history_id=latency_check_history_id,
            anchor_id=anchor["anchor_id"],
            user_anchor_id=anchor["id"],
            anchor_user_id=anchor["user_id"],
            commend_request_payload=data,
            register_anchor_location=location,
            latency_check_domain_name=host,
            commend_query_id=commend_query_id,
            created_date=now,
            modified_date=now,
        )

    # Thread pool execution
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_anchor, anchor) for anchor in rs]

        for future in as_completed(futures):
            record = future.result()
            bulk_insert_record_set.append(record)

    print("###################### bulk_insert_record_set #################", len(bulk_insert_record_set))

    LatencyCheckHistoryDetails.objects.bulk_create(bulk_insert_record_set)
'''
def LatencyMesurmentResult(obj):
    newSet = []
    updated_dataset = []
    rs = LatencyCheckHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, latency_check_history_id=obj.id, commend_query_id__isnull=False)
    rs = rs.values('id', 'commend_query_id', 'anchor_id', 'user_anchor', 'rtt_avg', 'rtt_max', 'rtt_min', 'anchor_id__db_url', 'anchor_id__storage_db')
    if rs:
        for lat in rs:
            dataSet = []
            #print('&&&&& anchor', lat['anchor_id'])
            #print('&&&&& LATENCY', lat['commend_query_id'])
            #print('&&&&& DB URL', lat['anchor_id__db_url'])
            #print('&&&&& STORAGE DB', lat['anchor_id__storage_db'])
            if lat['rtt_avg'] == 0 or lat['rtt_max'] == 0 or lat['rtt_min'] == 0:
                #print(lat['rtt_max'])
                # query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT rtt_avg, rtt_max, rtt_min FROM ping WHERE id='" + lat['commend_query_id'] + "'"
                query = str(lat['anchor_id__db_url']) + "/query?pretty=true&db=" + str(lat['anchor_id__storage_db']) + "&q=SELECT rtt_avg, rtt_max, rtt_min FROM ping WHERE id='" + lat['commend_query_id'] + "'"
                #print('$$$$$$$$$$$$$$$$$$', query)
                result = requests.get(query)
                if result.status_code == 200:
                    json_result = result.json()
                    # print('&&&&&&&&& json_result &&&&&&&&&&', json_result)
                    for val in json_result['results']:
                        if "series" in val:
                            for ser in val['series']:
                                if "values" in ser:
                                    for value in ser['values']:
                                        #print('&&&&&&&&& json_result &&&&&&&&&&',value)
                                        obj = LatencyCheckHistoryDetails.objects.filter(id=lat['id']).update(time=value[0], rtt_avg=value[1], rtt_max=value[2], rtt_min=value[3], execution_status='success')
                                        res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))}
                                        dataSet.append(res)

'''
def LatencyMesurmentResult(obj, max_workers=10):
    qs = (
        LatencyCheckHistoryDetails.objects
        .filter(
            is_deleted=False,
            is_blocked=False,
            latency_check_history_id=obj.id,
            commend_query_id__isnull=False
        )
        .values(
            'id',
            'commend_query_id',
            'anchor_id',
            'user_anchor',
            'rtt_avg',
            'rtt_max',
            'rtt_min',
            'anchor_id__db_url',
            'anchor_id__storage_db'
        )
        .iterator(chunk_size=1000)
    )

    session = requests.Session()
    updates = []

    def fetch_latency(lat):
        if lat['rtt_avg'] != 0 and lat['rtt_max'] != 0 and lat['rtt_min'] != 0:
            return None

        query = (
            f"{lat['anchor_id__db_url']}/query?pretty=true&db="
            f"{lat['anchor_id__storage_db']}"
            f"&q=SELECT rtt_avg, rtt_max, rtt_min FROM ping WHERE id='{lat['commend_query_id']}'"
        )

        try:
            result = session.get(query, timeout=5)
            if result.status_code != 200:
                return None

            json_result = result.json()

            for val in json_result.get('results', []):
                if "series" not in val:
                    continue
                for ser in val["series"]:
                    if "values" not in ser:
                        continue
                    for value in ser["values"]:
                        return {
                            "id": lat["id"],
                            "time": value[0],
                            "rtt_avg": value[1],
                            "rtt_max": value[2],
                            "rtt_min": value[3],
                        }
        except Exception:
            return None

    # Parallel execution
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_latency, lat) for lat in qs]

        for future in as_completed(futures):
            result = future.result()
            if result:
                updates.append(result)

    # Bulk update (fast)
    for batch in range(0, len(updates), 500):
        batch_data = updates[batch: batch + 500]

        objs = [
            LatencyCheckHistoryDetails(
                id=item["id"],
                time=item["time"],
                rtt_avg=item["rtt_avg"],
                rtt_max=item["rtt_max"],
                rtt_min=item["rtt_min"],
                execution_status='success',
                modified_date=timezone.now()
            )
            for item in batch_data
        ]

        LatencyCheckHistoryDetails.objects.bulk_update(
            objs,
            ["time", "rtt_avg", "rtt_max", "rtt_min", "execution_status", "modified_date"]
        )
class LatencyCheckAllAnchorView(APIView):
    '''
    def get(self,request, latencyid):
        from django.db.models import Avg
        latency_check_history_id = latencyid
        response_data = {}
        data = []
        exclude_array = [
            'nats-mum-anchor',
            'nats-blr-anchor',
            'nats-kol-anchor',
            'nats-gwh-anchor',
            'nats-moh-anchor'
        ]
        rs = LatencyCheckHistory.objects.filter(is_deleted=False, is_blocked=False, latency_measurement_id=latency_check_history_id).first()
        if rs:
            LatencyMesurmentResult(rs)
            # print('&&&&&&&&&&&&&&&&&&', qs.query)
            qs = LatencyCheckHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, latency_check_history_id=rs.id, commend_query_id__isnull=False).exclude(rtt_avg =0, rtt_max=0, rtt_min=0).exclude(anchor_id__anchor_name__in =exclude_array).order_by('register_anchor_location').values('register_anchor_location').annotate(count=Count('id'), avg_rtt_avg=Avg('rtt_avg'), avg_rtt_max=Avg('rtt_max'), avg_rtt_min=Avg('rtt_min'))

            location_qs = LatencyCheckHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, latency_check_history_id=rs.id, commend_query_id__isnull=False).exclude(rtt_avg =0, rtt_max=0, rtt_min=0).exclude(anchor_id__anchor_name__in =exclude_array).order_by('register_anchor_location').values('register_anchor_location', 'user_anchor_id__latitude', 'user_anchor_id__longitude', 'user_anchor_id__address', 'anchor_id__anchor_name', 'rtt_avg', 'rtt_max', 'rtt_min').annotate(count=Count('id'))
            city = {}
            if location_qs:
                for n in location_qs:
                    hit_count =  n['count']
                    keys = city.keys()
                    if n['register_anchor_location'] in city:
                        for key in city:
                            # print(city)
                            if key == n['register_anchor_location']:
                                # print('KEY',key)
                                # print('Ncity', n['city'])
                                city[key].append({'lat': float(n['user_anchor_id__latitude']), 'lng': float(n['user_anchor_id__longitude']), 'count':int(hit_count), 'anchor_name':n['anchor_id__anchor_name'], 'anchor_register_address':n['user_anchor_id__address'], 'rtt_max':n['rtt_max'], 'rtt_avg':n['rtt_avg'], 'rtt_min':n['rtt_min']})
                    else:
                        city[n['register_anchor_location']] = []
                        city[n['register_anchor_location']].append({'lat': float(n['user_anchor_id__latitude']), 'lng': float(n['user_anchor_id__longitude']), 'count':int(hit_count), 'anchor_name':n['anchor_id__anchor_name'], 'anchor_register_address':n['user_anchor_id__address'], 'rtt_max':n['rtt_max'], 'rtt_avg':n['rtt_avg'], 'rtt_min':n['rtt_min']})

            response_data['status'] = 1
            response_data['message'] = 'Latency found.'
            response_data['data'] = list(qs)
            response_data['city_location'] = city
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)
    '''

    def get(self, request, latencyid):
        from django.db.models import Avg, Count

        response_data = {}

        exclude_array = [
            "nats-mum-anchor",
            "nats-blr-anchor",
            "nats-kol-anchor",
            "nats-gwh-anchor",
            "nats-moh-anchor",
        ]

        rs = (
            LatencyCheckHistory.objects
            .filter(
                is_deleted=False,
                is_blocked=False,
                latency_measurement_id=latencyid
            )
            .only("id")
            .first()
        )

        if not rs:
            return JsonResponse({
                "status": 0,
                "message": "No record found in our database.",
                "data": []
            }, status=200)

        # Run async measurement update
        LatencyMesurmentResult(rs)

        # Base queryset (single optimized query path)
        base_qs = (
            LatencyCheckHistoryDetails.objects
            .filter(
                is_deleted=False,
                is_blocked=False,
                latency_check_history_id=rs.id,
                commend_query_id__isnull=False
            )
            .exclude(
                rtt_avg=0,
                rtt_max=0,
                rtt_min=0
            )
            .exclude(
                anchor_id__anchor_name__in=exclude_array
            )
            .select_related("anchor_id", "user_anchor_id")
        )

        # Aggregation query (fast)
        aggregated = list(
            base_qs
            .values("register_anchor_location")
            .annotate(
                count=Count("id"),
                avg_rtt_avg=Avg("rtt_avg"),
                avg_rtt_max=Avg("rtt_max"),
                avg_rtt_min=Avg("rtt_min")
            )
            .order_by("register_anchor_location")
        )

        # Location details query
        location_qs = (
            base_qs
            .values(
                "register_anchor_location",
                "user_anchor_id__latitude",
                "user_anchor_id__longitude",
                "user_anchor_id__address",
                "anchor_id",
                "anchor_id__anchor_name",
                "rtt_avg",
                "rtt_max",
                "rtt_min"
            )
            .annotate(count=Count("id"))
            .iterator(chunk_size=1000)  # critical for performance
        )

        city = {}

        isp_map = dict(
            AnchorIpDetails.objects.values_list("anchor_id", "isp")
        )

        for n in location_qs:
            loc = n["register_anchor_location"]
            anchor_id = n["anchor_id"]

            city.setdefault(loc, []).append({
                "lat": float(n["user_anchor_id__latitude"]),
                "lng": float(n["user_anchor_id__longitude"]),
                "count": int(n["count"]),
                "anchor_name": n["anchor_id__anchor_name"],
                "isp": isp_map.get(anchor_id),
                "anchor_register_address": n["user_anchor_id__address"],
                "rtt_max": n["rtt_max"],
                "rtt_avg": n["rtt_avg"],
                "rtt_min": n["rtt_min"],
            })

        response_data["status"] = 1
        response_data["message"] = "Latency found."
        response_data["data"] = aggregated
        response_data["city_location"] = city

        return JsonResponse(response_data, status=200)
    def post(self,request):
        requestData = request.data
        #print(requestData)
        response_data = {}
        # rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active", anchor_id__is_online=True)
        # rs = rs.order_by('-id')
        # rs = rs.values('id', 'lease_id', 'anchor_id', 'location', 'user_id')
        rs = get_active_measurement_anchors_data()
        if rs:
            # print('add_serve_measurement', obj_id)
            serve_measurement_id = get_random_string(length=10)
            print('add_serve_measurement', serve_measurement_id)
            obj = LatencyCheckHistory.objects.create(
                serve_ip_details_id=requestData['serve_detail_id'],
                latency_check_domain_name=requestData['domain'],
                latency_measurement_id=serve_measurement_id,
                created_date=timezone.now(),
                modified_date=timezone.now()
            )
            latency_check_measurement(obj.id, requestData['domain'], rs)
            # return serve_measurement_id
            response_data['status'] = 1
            response_data['message'] = 'Latency executed successfully.'
            response_data['data'] = serve_measurement_id
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'There is currently no anchor in lease.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

def FindStateShortName(state_name):
    state_obj = [{'state_name':'Andaman and Nicobar Islands','abbreviation':'AN','alternate_abbreviation':'IN-AN'},{'state_name':'Andhra Pradesh','abbreviation':'AP','alternate_abbreviation':'IN-AP'},{'state_name':'Arunachal Pradesh','abbreviation':'AR','alternate_abbreviation':'IN-AR'},{'state_name':'Assam','abbreviation':'AS','alternate_abbreviation':'IN-AS'},{'state_name':'Bihar','abbreviation':'BR','alternate_abbreviation':'IN-BR'},{'state_name':'Chandigarh','abbreviation':'CH','alternate_abbreviation':'IN-CH'},{'state_name':'Chhattisgarh','abbreviation':'CT','alternate_abbreviation':'IN-CT'},{'state_name':'Dadra and Nagar Haveli','abbreviation':'DN','alternate_abbreviation':'IN-DN'},{'state_name':'Daman and Diu','abbreviation':'DD','alternate_abbreviation':'IN-DD'},{'state_name':'Delhi','abbreviation':'DL','alternate_abbreviation':'IN-DL'},{'state_name':'Goa','abbreviation':'GA','alternate_abbreviation':'IN-GA'},{'state_name':'Gujarat','abbreviation':'GJ','alternate_abbreviation':'IN-GJ'},{'state_name':'Haryana','abbreviation':'HR','alternate_abbreviation':'IN-HR'},{'state_name':'Himachal Pradesh','abbreviation':'HP','alternate_abbreviation':'IN-HP'},{'state_name':'Jammu and Kashmir','abbreviation':'JK','alternate_abbreviation':'IN-JK'},{'state_name':'Jharkhand','abbreviation':'JH','alternate_abbreviation':'IN-JH'},{'state_name':'Karnataka','abbreviation':'KA','alternate_abbreviation':'IN-KA'},{'state_name':'Kerala','abbreviation':'KL','alternate_abbreviation':'IN-KL'},{'state_name':'Lakshadweep','abbreviation':'LD','alternate_abbreviation':'IN-LD'},{'state_name':'Madhya Pradesh','abbreviation':'MP','alternate_abbreviation':'IN-MP'},{'state_name':'Maharashtra','abbreviation':'MH','alternate_abbreviation':'IN-MH'},{'state_name':'Manipur','abbreviation':'MN','alternate_abbreviation':'IN-MN'},{'state_name':'Meghalaya','abbreviation':'ML','alternate_abbreviation':'IN-ML'},{'state_name':'Mizoram','abbreviation':'MZ','alternate_abbreviation':'IN-MZ'},{'state_name':'Nagaland','abbreviation':'NL','alternate_abbreviation':'IN-NL'},{'state_name':'Odisha','abbreviation':'OR','alternate_abbreviation':'IN-OR'},{'state_name':'Puducherry','abbreviation':'PY','alternate_abbreviation':'IN-PY'},{'state_name':'Punjab','abbreviation':'PB','alternate_abbreviation':'IN-PB'},{'state_name':'Rajasthan','abbreviation':'RJ','alternate_abbreviation':'IN-RJ'},{'state_name':'Sikkim','abbreviation':'SK','alternate_abbreviation':'IN-SK'},{'state_name':'Tamil Nadu','abbreviation':'TN','alternate_abbreviation':'IN-TN'},{'state_name':'Telangana','abbreviation':'TG','alternate_abbreviation':'IN-TG'},{'state_name':'Tripura','abbreviation':'TR','alternate_abbreviation':'IN-TR'},{'state_name':'Uttar Pradesh','abbreviation':'UP','alternate_abbreviation':'IN-UP'},{'state_name':'Uttarakhand','abbreviation':'UT','alternate_abbreviation':'IN-UT'},{'state_name':'West Bengal','abbreviation':'WB','alternate_abbreviation':'IN-WB'}]
    state_code_namme = ''
    for s in state_obj:
        if state_name == s['state_name']:
            state_code_namme = s['abbreviation']

    return state_code_namme

class SunbustFormatLatencyCheckAllAnchorView(APIView):
    def get(self,request, latencyid):
        from django.db.models import Avg
        latency_check_history_id = latencyid
        response_data = {}
        data = []
        exclude_array = [
            'nats-mum-anchor',
            'nats-blr-anchor',
            'nats-kol-anchor',
            'nats-gwh-anchor',
            'nats-moh-anchor'
        ]
        
        rs = LatencyCheckHistory.objects.filter(is_deleted=False, is_blocked=False, latency_measurement_id=latency_check_history_id).first()
        if rs:
            LatencyMesurmentResult(rs)
            rs_by_state = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location_register_status='registered', country__isnull=False, administrative_area_level_1__isnull=False, location__isnull=False, address__isnull=False, anchor_id__is_online=True, anchor_id__anchor_status='active', anchor_id__version=1).values('administrative_area_level_1').annotate(state_anchor_count=Count('id'))
            if rs_by_state:
                for s in rs_by_state:
                    rs_by_city = rs_by_city = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, location_register_status='registered', country__isnull=False, administrative_area_level_1__isnull=False, administrative_area_level_2__isnull=False, location__isnull=False, address__isnull=False, administrative_area_level_1=s['administrative_area_level_1'], anchor_id__is_online=True, anchor_id__anchor_status='active', anchor_id__version=1).values('location').annotate(city_anchor_count=Count('id'))

                    state_color_code = ''.join(random.choice('0123456789') for _ in range(6))
                    city_children = []
                    state_rtt_avg_sum = 0
                    state_total_anchor_count = 0
                    state_anchor_name_str = ''
                    if rs_by_city:
                        # s['children'] = list(rs_by_city)
                        chield_city = []
                        for c in rs_by_city:
                            location_qs = LatencyCheckHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, latency_check_history_id=rs.id, commend_query_id__isnull=False, register_anchor_location=c['location'].lower())
                            location_qs = location_qs.exclude(rtt_avg =0, rtt_max=0, rtt_min=0)
                            location_qs = location_qs.exclude(anchor_id__anchor_name__in =exclude_array)
                            location_qs = location_qs.order_by('register_anchor_location')
                            location_qs = location_qs.values('register_anchor_location', 'user_anchor_id__latitude', 'user_anchor_id__longitude', 'user_anchor_id__address', 'anchor_id__anchor_name', 'rtt_avg', 'rtt_max', 'rtt_min' , 'user_anchor_id__administrative_area_level_1' , 'user_anchor_id__administrative_area_level_2' , 'user_anchor_id__sublocality_level_1').annotate(count=Count('id'))

                            city_color_code = ''.join(random.choice('0123456789') for _ in range(6))
                            if location_qs:
                                children = []
                                city_rtt_avg_sum = 0
                                # print(len(location_qs))
                                state_total_anchor_count = float(state_total_anchor_count) + float(len(location_qs))
                                total_city_anchor_count = 0
                                anchor_name_str = ''
                                for l in location_qs:
                                    ground_color_code = ''.join(random.choice('0123456789') for _ in range(6))
                                    city_rtt_avg_sum = float(city_rtt_avg_sum) + float(l['rtt_avg'])
                                    state_rtt_avg_sum = float(state_rtt_avg_sum) + float(l['rtt_avg'])
                                    children.append({
                                        'name': l['anchor_id__anchor_name'] + ' ( '+str(round(l['rtt_avg'], 2))+' )',
                                        'location': l['user_anchor_id__address'],
                                        'value': l['count'],
                                        'itemStyle': { 'color': '#'+ground_color_code },
                                        'anchors': l['anchor_id__anchor_name'] + ' ( '+str(round(l['rtt_avg'], 2))+' )',
                                    })
                                    anchor_name_str += l['user_anchor_id__administrative_area_level_2']+': '+ l['anchor_id__anchor_name'] + ' ( '+str(round(l['rtt_avg'], 2))+' ) <br />'
                                    state_anchor_name_str += l['user_anchor_id__administrative_area_level_2']+': '+l['anchor_id__anchor_name'] + ' ( '+str(round(l['rtt_avg'], 2))+' ) <br />'
                                    total_city_anchor_count = total_city_anchor_count+1
                                # print('Location Count', c['location'], '******', a_count)
                                    # l['children'] = children
                                city_children.append({
                                   'name': c['location'] + ' ( '+str( round(float(city_rtt_avg_sum) / float(total_city_anchor_count), 2))+' )',
                                   'location': c['location'] + ' ( '+str( round(float(city_rtt_avg_sum) / float(total_city_anchor_count), 2))+' )',
                                    'value': total_city_anchor_count,
                                    'itemStyle': { 'color': '#'+city_color_code },
                                    'anchors': anchor_name_str,
                                    'children': children 
                                })
                                chield_city.append({'location': c['location'], 'city_anchor_count': c['city_anchor_count'], 'children': list(location_qs)})
                                # c['children'] = list(location_qs)
                                s['children'] = chield_city
                                # data.append({
                                #     'name': FindStateShortName(s['administrative_area_level_1']),
                                #     'value': s['state_anchor_count'],
                                #     'itemStyle': { 'color': '#'+state_color_code },
                                #     'children': [{
                                #         'name': c['location'],
                                #         'value': c['city_anchor_count'],
                                #         'itemStyle': { 'color': '#'+city_color_code },
                                #         'children': children
                                #     }]
                                # })
                    
                        if len(city_children) > 0:
                            # print('State Anchor Count', s['administrative_area_level_1'], '******', state_total_anchor_count)
                            # print('State Count', s['administrative_area_level_1'], '******', s['state_anchor_count'])
                            # round(5.76543, 2)
                            data.append({
                                'name': FindStateShortName(s['administrative_area_level_1']) + ' ( ' + str(round(float(state_rtt_avg_sum) / float(state_total_anchor_count), 2)) + ' )',
                                'location': s['administrative_area_level_1'] + ' ( ' + str(round(float(state_rtt_avg_sum) / float(state_total_anchor_count), 2)) + ' )',
                                # 'value': s['state_anchor_count'],
                                'itemStyle': { 'color': '#'+state_color_code },
                                'children': city_children,
                                'anchors': state_anchor_name_str,
                            })
            response_data['status'] = 1
            response_data['message'] = 'Latency found.'
            response_data['data'] = list(rs_by_state)
            response_data['newdata'] = data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)


class ServeResearchView(APIView):
    def get(self,request):
        response_data = {}
        data = []
        mesurHisDtlqs = ServeMeasurementHistoryDetails.objects.filter(is_deleted=False, is_blocked=False).exclude(rtt_avg =0).order_by('serve_measurement_history_id').values_list('serve_measurement_history_id')
        # print('&&&&&&&&&&&&&&&&&&', mesurHisDtlqs.query)
        city = {}
        total_count = 0
        if mesurHisDtlqs:
            mesurHisqs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, id__in=mesurHisDtlqs).order_by('serve_location').values_list('serve_ip_details_id')
            if mesurHisqs:
                rs1 = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, city__isnull=False, latitude__isnull=False, longitude__isnull=False, id__in=mesurHisqs).order_by('city').values('city', 'latitude', 'longitude', 'id').annotate(count=Sum('request_counter'))
                #print('&&&&&&&&&444444444444444444&&&&&&&&&', rs1.query)
                if mesurHisqs:
                    for n in rs1:
                        hit_count =  n['count']
                        total_count +=  hit_count
                        keys = city.keys()
                        if n['city'] in city:
                            for key in city:
                                # print(city)
                                if key == n['city']:
                                    city[key].append({'lat': float(n['latitude']), 'lng': float(n['longitude']), 'count':int(hit_count)})
                        else:
                            city[n['city']] = []
                            city[n['city']].append({'lat': float(n['latitude']), 'lng': float(n['longitude']), 'count':int(hit_count)})
            data.append({'citis':city, 'total_hits': total_count})
            # data.append({'circledata': list(rs), 'markerdata':list(latlong)})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            # response_data['latlong'] = list(latlong)
            response_data['data'] = data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class ServeLatencyAllCityView(APIView):
    def get(self,request):
        from django.db.models import Avg
        response_data = {}
        data = []
        labels = []
        Bengaluru = []
        Guwahati = []
        Kolkata = []
        Mohali = []
        Mumbai = []
        Sidrs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, latitude__isnull=False, longitude__isnull=False, city__isnull=False).order_by('city').values('city').annotate(count=Sum('request_counter'))
        #print('&&&&&&&&&&&&&&&&&&&& ServeMeasurementHistory &&&&&&&&&&&&&&&&&', Sidrs.query)
        if Sidrs:
            for n in Sidrs:
                rs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, serve_ip_details_id__serve_location__isnull=False, serve_ip_details_id__latitude__isnull=False, serve_ip_details_id__longitude__isnull=False, serve_ip_details_id__city__isnull=False,  serve_ip_details_id__city__contains=n['city']).values_list('id', flat=True)
                # print('&&&&&&&&&&&&&&&&&&&& ServeMeasurementHistory &&&&&&&&&&&&&&&&&', rs.query)
                if rs:
                    qs = ServeMeasurementHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, serve_measurement_history_id__in=rs).\
                    exclude(rtt_avg =0).\
                    extra({'created_day':"date(created_date)"}).\
                    order_by('vartual_anchor_location').\
                    values('vartual_anchor_location').\
                    annotate(avg_latency=Avg('rtt_avg'))
                    if qs:
                        labels.append(n['city'])
                        for l in qs:
                            if l['vartual_anchor_location'] == 'Bengaluru':
                                Bengaluru.append(round(l['avg_latency'], 3))
                            if l['vartual_anchor_location'] == 'Guwahati':
                                Guwahati.append(round(l['avg_latency'], 3))
                            if l['vartual_anchor_location'] == 'Kolkata':
                                Kolkata.append(round(l['avg_latency'], 3))
                            if l['vartual_anchor_location'] == 'Mohali':
                                Mohali.append(round(l['avg_latency'], 3))
                            if l['vartual_anchor_location'] == 'Mumbai':
                                Mumbai.append(round(l['avg_latency'], 3))
                # print('&&&&&&&&&&&&&&&&&&', qs.query)
            data.append({'labels': labels, 'Bengaluru':Bengaluru, 'Guwahati': Guwahati, 'Kolkata':Kolkata, 'Mohali': Mohali, 'Mumbai': Mumbai})
            response_data['status'] = 1
            response_data['message'] = 'Latency found.'
            response_data['data'] = data
            # response_data['ids'] = list(qs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class ServeLatencyCheckView(APIView):
    def get(self,request):
        from django.db.models import Avg
        from django.db.models.functions import Lower
        response_data = {}
        # rs = LatencyCheckHistory.objects.filter(is_blocked = False, is_deleted = False, latency_check_domain_name__isnull = False).exclude(latency_check_domain_name="").exclude(latency_check_history_id__rtt_avg=0).order_by('latency_check_domain_name')
        rs = LatencyCheckHistoryDetails.objects.filter(is_blocked = False, is_deleted = False, latency_check_domain_name__isnull = False).\
        exclude(latency_check_domain_name="").\
        exclude(rtt_avg=0).\
        annotate(domain_lower=Lower('latency_check_domain_name')).\
        order_by('domain_lower').\
        distinct('domain_lower').\
        values_list('domain_lower', flat=True)
        print(rs.query)
        if rs:
            # serializer = LatencyCheckHistoryDetailsSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'record found.'
            response_data['data'] = list(rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        from django.db.models.functions import TruncMonth, TruncHour
        from datetime import datetime, timedelta
        from datetime import date
        import datetime
        response_data = {}
        requestData = request.data
        print(requestData)
        locationArray = {}
        data = []
        ### Get Anchor Location ####
        anchorLocationrs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, location__isnull=False, status="active", location_register_status="registered")
        anchorLocationrs = anchorLocationrs.values('location')
        anchorLocationrs = anchorLocationrs.annotate(anchor_count=Count('location'))
        anchorLocationrs = anchorLocationrs.order_by('location')
        if anchorLocationrs:
            for al in anchorLocationrs:
                locationArray[al["location"]] = []
        latencyHisDtlqs = LatencyCheckHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, latency_check_domain_name__icontains=requestData['domain']).exclude(rtt_avg=0).order_by("register_anchor_location").values('register_anchor_location').annotate(count=Count('register_anchor_location'))

        rs = LatencyCheckHistory.objects.filter(is_deleted=False, is_blocked=False)
        if requestData['domain'] == 'all':
            rs = rs.filter(created_date__lte=datetime.datetime.today(), created_date__gt=datetime.datetime.today() - datetime.timedelta(days=requestData['duration']))
        else:
            rs = rs.filter(latency_check_domain_name__icontains=requestData['domain'])
            rs = rs.filter(created_date__lte=datetime.datetime.today(), created_date__gt=datetime.datetime.today() - datetime.timedelta(days=int(requestData['duration'])))
        rs = rs.order_by('created_date').values('created_date', 'id')
        rs = rs.annotate(data_count=Count('created_date'))
        # print('&&&&&&&&&&&&&&&&&&', dataset.query)
        total_count = 0
        if rs:
            labels = []
            for n in rs:
                qs = LatencyCheckHistoryDetails.objects.filter(is_deleted=False, is_blocked=False, latency_check_history_id = n['id']).\
                order_by('register_anchor_location').\
                values('register_anchor_location').\
                annotate(avg_latency=Avg('rtt_avg'))
                if qs:
                    labels.append(n['created_date'])
                    if len(locationArray) > 0:
                        for key in locationArray:
                            for r in qs:
                                if key == r['register_anchor_location']:
                                    locationArray[key].append(round(r['avg_latency'], 3))


            data.append({'labels': labels, 'data': locationArray})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            # response_data['count'] = list(dataset)
            # response_data['Attay_list'] = locationArray
            response_data['data'] = data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def put(self,request):
        from django.db.models.functions import TruncYear, TruncMonth, TruncWeek, TruncQuarter, TruncDate, TruncDay, TruncHour
        from django.db.models.functions import ExtractMonth
        from datetime import datetime, timedelta
        from datetime import date
        import datetime
        response_data = {}
        requestData = request.data
        print(requestData)
        locationArray = {}
        data = []
        ## Set query param on condition base ##
        q_load = {}
        date_filter = {}

        if requestData['duration'] == 'yearly':
            q_load = {'month':TruncYear('created_date')}
            date_filter = {'created_date__lte':datetime.datetime.today(), 'created_date__gte':datetime.datetime.today() - datetime.timedelta(days=3650)}

        if requestData['duration'] == 'monthly':
            q_load = {'month':TruncMonth('created_date')}
            date_filter = {'created_date__lte':datetime.datetime.today(), 'created_date__gte':datetime.datetime.today() - datetime.timedelta(days=365)}

        if requestData['duration'] == 'quaterly':
            q_load = {'month':TruncQuarter('created_date')}
            date_filter = {'created_date__lte':datetime.datetime.today(), 'created_date__gte':datetime.datetime.today() - datetime.timedelta(days=365)}

        if requestData['duration'] == 'weekly':
            q_load = {'month':TruncWeek('created_date')}
            date_filter = {'created_date__lte':datetime.datetime.today(), 'created_date__gte':datetime.datetime.today() - datetime.timedelta(days=365)}

        if requestData['duration'] == 'dayly':
            q_load = {'month':TruncDay('created_date')}
            date_filter = {'created_date__lte':datetime.datetime.today(), 'created_date__gte':datetime.datetime.today() - datetime.timedelta(days=30)}

        if requestData['duration'] == 'hourly':
            q_load = {'month':TruncHour('created_date')}
            date_filter = {'created_date__lte':datetime.datetime.today(), 'created_date__gte':datetime.datetime.today() - datetime.timedelta(days=30)}


        ### Get Anchor Location ####
        anchorLocationrs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, location__isnull=False, status="active", location_register_status="registered")
        anchorLocationrs = anchorLocationrs.values('location')
        anchorLocationrs = anchorLocationrs.annotate(anchor_count=Count('location'))
        anchorLocationrs = anchorLocationrs.order_by('location')
        if anchorLocationrs:
            for al in anchorLocationrs:
                locationArray[al["location"]] = []
        ##### TEST QUERY #####
        querySet = LatencyCheckHistoryDetails.objects.filter(is_deleted=False, is_blocked=False,latency_check_domain_name__icontains=requestData['domain']).filter(**date_filter).\
        annotate(**q_load).\
        values('month').\
        annotate(avg_latency=Avg('rtt_avg')).\
        order_by('register_anchor_location').\
        order_by('month').\
        values('month', 'avg_latency', 'register_anchor_location')
        print('&&&&&&&&& querySet &&&&&&&&&', querySet.query) 
        ###### TEST QUERY #######
        if querySet:
            labels = []
            for n in querySet:
                if (len(list(filter (lambda x : x == n['month'], labels))) <= 0):
                    labels.append(n['month'])
                if len(locationArray) > 0:
                    for key in locationArray:
                        if key == n['register_anchor_location']:
                            locationArray[key].append(round(n['avg_latency'], 3))

            data.append({'labels': labels, 'data': locationArray})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            # response_data['count'] = list(querySet)
            # response_data['Attay_list'] = locationArray
            response_data['data'] = data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class ServeRoutingDetoreView(APIView):
    def get(self,request):
        response_data = {}
        data = []
        ### Telephone Circle Area Array ###
        zone_array = {
            'Mohali':['Punjab', 'Chandigarh'],
            'Guwahati':['Assam'],
            'Kolkata':['Kolkata'],
            'Mumbai':['Mumbai', 'New Mumbai', 'Maharashtra', 'Goa'],
            'Bengaluru':['Karnataka', 'Bengaluru']
        }

        ### Predefine Zone Array ###
        zone_array = {
            'Mohali':[
                'Delhi',
                'Haryana', 
                'Rajasthan', 
                'Punjab', 
                'Himachal Pradesh', 
                'Jammu & Kashmir',
                'Chandigarh', 
                'Uttar Pradesh', 
                'Uttaranchal', 
                'Madhya Pradesh', 
                'Chhattisgarh'
                ],

            'Guwahati':[
                'Assam', 
                'Meghalaya', 
                'Sikkim', 
                'Arunachal Pradesh', 
                'Nagaland', 
                'Tripura', 
                'Mizoram', 
                'Manipur'
                ],

            'Kolkata':[
                'West Bengal', 
                'Bihar', 
                'Jharkhand', 
                'Odisha', 
                'Andaman Nicobar' 
                ],

            'Mumbai':[
                'Maharashtra', 
                'Gujarat', 
                'Goa', 
                'Dadra & Nagarhaweli',
                'Daman & Diu'
                ],

            'Bengaluru':[
                'Tamil Nadu', 
                'Kerala', 
                'Pondicherry', 
                'Lakshadweep', 
                'Telangana', 
                'Andhra Pradesh', 
                'Karnataka'
                ]
        }
        qs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False, country='IN').exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('serve_location').values('serve_location').annotate(total_hit_count=Sum('request_counter'))
        print('&&&&&&&&&&&&&&&&&&', qs.query)
        if qs:
            for l in qs:
                l['inside_zone_hit_count'] = 0
                l['outside_zone_hit_count'] = 0
                rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, serve_location=l['serve_location'], country__isnull=False, country='IN').exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('state').values('state').annotate(count=Sum('request_counter'))

                print('&&&&&&&&&^^^^^^^^^^^^^^^^^^^&&&&&&&&&', rs.query)
                if rs:
                    for key in zone_array:
                        if key == l['serve_location']:   
                            # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', zone_array[key], '***** SERVE LOCATION', l['serve_location'])
                            for s in rs:
                                if s['state'] in zone_array[key]:
                                    l['inside_zone_hit_count'] += s['count']
                                    # print('State Have', s['state'], '***** SERVE LOCATION', l['serve_location'])
                                else:
                                    # print('State Have Not', s['state'], '***** Count', s['count'])
                                    l['outside_zone_hit_count'] += s['count']
                # data.append({l['serve_location']:list(rs)})
            latlongrs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False, country='IN', state='West Bengal').exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('-city').values('latitude', 'longitude').distinct('city')

            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['data'] = list(qs)
            response_data['latlong'] = list(latlongrs)
            # response_data['Zone'] = zone_array
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        response_data = {}
        requestData = request.data
        data = []
        print(requestData)
        ### Predefine Zone Array ###
        zone_array = {
            'Mohali':['Delhi', 'Haryana', 'Rajasthan', 'Punjab', 'Himachal Pradesh', 'Jammu & Kashmir', 'Chandigarh', 'Uttar Pradesh', 'Uttaranchal', 'Madhya Pradesh', 'Chhattisgarh'],
            'Guwahati':['Assam', 'Meghalaya', 'Sikkim', 'Arunachal Pradesh', 'Nagaland', 'Tripura', 'Mizoram', 'Manipur'],
            'Kolkata':['West Bengal', 'Bihar', 'Jharkhand', 'Odisha', 'Andaman Nicobar' ],
            'Mumbai':['Maharashtra', 'Gujarat', 'Goa', 'Dadra & Nagarhaweli','Daman & Diu'],
            'Bengaluru':['Tamil Nadu', 'Kerala', 'Pondicherry', 'Lakshadweep', 'Telangana', 'Andhra Pradesh', 'Karnataka']
        }
        qs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False, country='IN', created_date__lte=requestData['to_date'], created_date__gt=requestData['from_date']).\
        exclude(serve_location ='localhost').\
        exclude(serve_location ='Localhost').\
        order_by('serve_location').\
        values('serve_location').\
        annotate(total_hit_count=Sum('request_counter'))
        print('&&&&&&&&&&&&&&&&&&', qs.query)
        if qs:
            for l in qs:
                l['inside_zone_hit_count'] = 0
                l['outside_zone_hit_count'] = 0
                rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, serve_location=l['serve_location'], country__isnull=False, country='IN', created_date__lte=requestData['to_date'], created_date__gte=requestData['from_date']).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('state').values('state').annotate(count=Sum('request_counter'))
                if rs:
                    for key in zone_array:
                        if key == l['serve_location']:   
                            # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', zone_array[key], '***** SERVE LOCATION', l['serve_location'])
                            for s in rs:
                                if s['state'] in zone_array[key]:
                                    l['inside_zone_hit_count'] += s['count']
                                    # print('State Have', s['state'], '***** SERVE LOCATION', l['serve_location'])
                                else:
                                    # print('State Have Not', s['state'], '***** Count', s['count'])
                                    l['outside_zone_hit_count'] += s['count']
                # data.append({l['serve_location']:list(rs)})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['data'] = list(qs)
            # response_data['data'] = data
            # response_data['Zone'] = zone_array
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class TelephoneCircleRoutingDetoreView(APIView):
    def get(self,request):
        response_data = {}
        data = []
        detour_data = {}
        ### Telephone Circle Area Array ###
        zone_array = {
            'Mohali':['Punjab', 'Chandigarh'],
            'Guwahati':['Assam'],
            'Kolkata':['Kolkata'],
            'Mumbai':['Mumbai', 'New Mumbai', 'Maharashtra', 'Goa'],
            'Bengaluru':['Karnataka', 'Bengaluru']
        }
        qs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('serve_location').values('serve_location').annotate(total_hit_count=Sum('request_counter'))
        print('&&&&&&&&&&&&&&&&&&', qs.query)
        if qs:
            for l in qs:
                l['inside_zone_hit_count'] = 0
                l['outside_zone_hit_count'] = 0
                rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, serve_location=l['serve_location'], country__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('city').values('city').annotate(count=Sum('request_counter'))

                print('&&&&&&&&&^^^^^^^^^^^^^^^^^^^&&&&&&&&&', rs.query)
                if rs:
                    for key in zone_array:
                        if key == l['serve_location']:   
                            # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', zone_array[key], '***** SERVE LOCATION', l['serve_location'])
                            for s in rs:
                                if s['city'] in zone_array[key]:
                                    l['inside_zone_hit_count'] += s['count']
                                    # print('State Have', s['state'], '***** SERVE LOCATION', l['serve_location'])
                                else:
                                    # print('State Have Not', s['state'], '***** Count', s['count'])
                                    l['outside_zone_hit_count'] += s['count']
                # data.append({l['serve_location']:list(rs)})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['data'] = list(qs)
            response_data['detour'] = list(rs)
            # response_data['data'] = data
            # response_data['Zone'] = zone_array
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        from datetime import datetime
        response_data = {}
        requestData = request.data
        data = []
        print(requestData)
        # fd = datetime.datetime(requestData['from_date'])
        # d = datetime.fd
        # print(fd)
        ### Telephone Circle Area Array ###
        zone_array = {
            'Mohali':['Punjab', 'Chandigarh'],
            'Guwahati':['Assam'],
            'Kolkata':['Kolkata'],
            'Mumbai':['Mumbai', 'New Mumbai', 'Maharashtra', 'Goa'],
            'Bengaluru':['Karnataka', 'Bengaluru']
        }
        # qs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False, modified_date__date__lte=requestData['to_date'], modified_date__date__gte=requestData['from_date']).\
        # exclude(serve_location ='localhost').\
        # exclude(serve_location ='Localhost').\
        # order_by('serve_location').\
        # values('serve_location').\
        # annotate(total_hit_count=Sum('request_counter'))
        qs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, city__isnull=False, country__isnull=False, created_date__date__gte=requestData['from_date'], created_date__date__lte=requestData['to_date']).\
        exclude(serve_location ='localhost').\
        exclude(serve_location ='Localhost').\
        order_by('serve_location').\
        values('serve_location').\
        annotate(total_hit_count=Count('id'))
        print('&&&&&&&&&&&&&&&&&&', qs.query)
        if qs:
            for l in qs:
                l['inside_zone_hit_count'] = 0
                l['outside_zone_hit_count'] = 0
                rs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, city__isnull=False, serve_location=l['serve_location'], country__isnull=False, created_date__date__gte=requestData['from_date'], created_date__date__lte=requestData['to_date']).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('city').values('city').annotate(count=Count('id'))
                # print('&&&&&&&&&&&&&&&&&&888888888888888888', rs.query)
                if rs:
                    for key in zone_array:
                        if key == l['serve_location']:   
                            # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', zone_array[key], '***** SERVE LOCATION', l['serve_location'])
                            for s in rs:
                                if s['city'] in zone_array[key]:
                                    l['inside_zone_hit_count'] += s['count']
                                    # print('State Have', s['state'], '***** SERVE LOCATION', l['serve_location'])
                                else:
                                    # print('State Have Not', s['state'], '***** Count', s['count'])
                                    l['outside_zone_hit_count'] += s['count']
                # data.append({l['serve_location']:list(rs)})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['data'] = list(qs)
            # response_data['data'] = data
            # response_data['Zone'] = zone_array
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class AsnWiseDetourServeLocationView(APIView):
    def get(self,request):
        # from itertools import chain
        response_data = {}
        data = []
        ### Telephone Circle Area Array ###
        zone_array = {
            'Mohali':['Punjab', 'Chandigarh'],
            'Guwahati':['Assam'],
            'Kolkata':['Kolkata', 'West Bengal'],
            'Mumbai':['Mumbai', 'New Mumbai', 'Maharashtra', 'Goa'],
            'Bengaluru':['Karnataka', 'Bengaluru']
        }
        states = ['Punjab', 'Chandigarh', 'Assam', 'Kolkata', 'West Bengal', 'Mumbai', 'New Mumbai', 'Maharashtra', 'Goa', 'Karnataka', 'Bengaluru']

        mohali_states = ['Punjab', 'Chandigarh']
        guwahati_states = ['Assam']
        kolkata_states = ['Kolkata', 'West Bengal']
        mumbai_states = ['Mumbai', 'New Mumbai', 'Maharashtra', 'Goa']
        bengaluru_states = ['Karnataka', 'Bengaluru']

        extend_mohali_states = ['Assam', 'Kolkata', 'West Bengal', 'Mumbai', 'New Mumbai', 'Maharashtra', 'Goa', 'Karnataka', 'Bengaluru']
        extend_guwahati_states = ['Punjab', 'Chandigarh', 'Kolkata', 'West Bengal', 'Mumbai', 'New Mumbai', 'Maharashtra', 'Goa', 'Karnataka', 'Bengaluru']
        extend_kolkata_states = ['Punjab', 'Chandigarh', 'Assam', 'Mumbai', 'New Mumbai', 'Maharashtra', 'Goa', 'Karnataka', 'Bengaluru']
        extend_mumbai_states = ['Punjab', 'Chandigarh', 'Assam', 'Kolkata', 'West Bengal', 'Karnataka', 'Bengaluru']
        extend_bengaluru_states = ['Punjab', 'Chandigarh', 'Assam', 'Kolkata', 'West Bengal', 'Mumbai', 'New Mumbai', 'Maharashtra', 'Goa']
        
        qs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False, org__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('serve_location').values('serve_location').annotate(total_hit_count=Sum('request_counter'))
        qs = qs.filter(reduce(lambda x, y: x | y, [Q(state=item) for item in states]))
        # print('&&&&&&&&&&&&&&&&&&', qs.query)
        if qs:
            for l in qs:
                l['inside_zone_hit_count'] = 0
                l['outside_zone_hit_count'] = 0
                rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, serve_location=l['serve_location'], country__isnull=False, org__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('state').values('state').annotate(count=Sum('request_counter'))
                rs = rs.filter(reduce(lambda x, y: x | y, [Q(state=item) for item in states]))

                # print('&&&&&&&&&^^^^^^^^^^^^^^^^^^^&&&&&&&&&', rs.query)
                if rs:
                    for key in zone_array:
                        if key == l['serve_location']:
                            inside_org_array = []
                            outside_org_array = []
                            # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', zone_array[key], '***** SERVE LOCATION', l['serve_location'])
                            if l['serve_location'] == 'Bengaluru':
                                inside_subset = bengaluru_states
                                outside_subset = extend_bengaluru_states
                            if l['serve_location'] == 'Guwahati':
                                inside_subset = guwahati_states
                                outside_subset = extend_guwahati_states
                            if l['serve_location'] == 'Kolkata':
                                inside_subset = kolkata_states
                                outside_subset = extend_kolkata_states
                            if l['serve_location'] == 'Mohali':
                                inside_subset = mohali_states
                                outside_subset = extend_mohali_states
                            if l['serve_location'] == 'Mumbai':
                                inside_subset = mumbai_states
                                outside_subset = extend_mumbai_states
                            # print('&&&&&&&&&^^^^^^^^^inside_subset^^^^^^^^^^&&&&&&&&&', inside_subset)
                            # print('&&&&&&&&&^^^^^^^^^outside_subset^^^^^^^^^^&&&&&&&&&', outside_subset)
                            for s in rs:
                                if s['state'] in zone_array[key]:
                                    l['inside_zone_hit_count'] += s['count']
                                    insiders = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, serve_location=l['serve_location'], country__isnull=False, org__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('org').values('org').annotate(count=Sum('request_counter'))
                                    insiders = insiders.filter(reduce(lambda x, y: x | y, [Q(state=item1) for item1 in inside_subset]))
                                    print('&&&&&&&&&^^^^^^^^^insiders^^^^^^^^^^&&&&&&&&&', insiders.query)
                                    if insiders:
                                        inside_org_array = (list(insiders))
                                    l['inside_zone_org'] = inside_org_array
                                    # print('State Have', s['state'], '***** SERVE LOCATION', l['serve_location'])
                                else:
                                    # print('State Have Not', s['state'], '***** Count', s['count'])
                                    l['outside_zone_hit_count'] += s['count']
                                    outsiders = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, serve_location=l['serve_location'], country__isnull=False, org__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost')
                                    outsiders = outsiders.filter(reduce(lambda x, y: x | y, [Q(state=item2) for item2 in outside_subset]))
                                    outsiders = outsiders.order_by('org').values('org').annotate(count=Sum('request_counter'))
                                    print('&&&&&&&&&^^^^^^^^^outsiders^^^^^^^^^^&&&&&&&&&', outsiders.query)
                                    if outsiders:
                                        outside_org_array = list(outsiders)

                                    l['outside_zone_org'] = outside_org_array
                # data.append({l['serve_location']:list(rs)})
            
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['data'] = list(qs)
            # response_data['detour'] = list(rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        response_data = {}
        requestData = request.data
        data = []
        filter_states = []

        mohali_states = ['Punjab', 'Chandigarh']
        guwahati_states = ['Assam']
        kolkata_states = ['Kolkata', 'West Bengal']
        mumbai_states = ['Mumbai', 'New Mumbai', 'Maharashtra', 'Goa']
        bengaluru_states = ['Karnataka', 'Bengaluru']

        extend_mohali_states = ['Assam', 'Kolkata', 'West Bengal', 'Mumbai', 'New Mumbai', 'Maharashtra', 'Goa', 'Karnataka', 'Bengaluru']
        extend_guwahati_states = ['Punjab', 'Chandigarh', 'Kolkata', 'West Bengal', 'Mumbai', 'New Mumbai', 'Maharashtra', 'Goa', 'Karnataka', 'Bengaluru']
        extend_kolkata_states = ['Punjab', 'Chandigarh', 'Assam', 'Mumbai', 'New Mumbai', 'Maharashtra', 'Goa', 'Karnataka', 'Bengaluru']
        extend_mumbai_states = ['Punjab', 'Chandigarh', 'Assam', 'Kolkata', 'West Bengal', 'Karnataka', 'Bengaluru']
        extend_bengaluru_states = ['Punjab', 'Chandigarh', 'Assam', 'Kolkata', 'West Bengal', 'Mumbai', 'New Mumbai', 'Maharashtra', 'Goa']
        ## Filter Variable Set
        if requestData['type'] == 'detour':
            if requestData['location'] == 'Guwahati':
                filter_states = extend_guwahati_states
            if requestData['location'] == 'Mohali':
                filter_states = extend_mohali_states
            if requestData['location'] == 'Kolkata':
                filter_states = extend_kolkata_states
            if requestData['location'] == 'Mumbai':
                filter_states = extend_mumbai_states
            if requestData['location'] == 'Bengaluru':
                filter_states = extend_bengaluru_states
        else:
            if requestData['location'] == 'Guwahati':
                filter_states = guwahati_states
            if requestData['location'] == 'Mohali':
                filter_states = mohali_states
            if requestData['location'] == 'Kolkata':
                filter_states = kolkata_states
            if requestData['location'] == 'Mumbai':
                filter_states = mumbai_states
            if requestData['location'] == 'Bengaluru':
                filter_states = bengaluru_states

        rs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False, org__isnull=False, serve_location=requestData['location']).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('serve_location').values('serve_location').annotate(total_hit_count=Sum('request_counter'))
        rs = rs.filter(reduce(lambda x, y: x | y, [Q(state=item) for item in filter_states]))
        if rs:
            for n in rs:
                qs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False, serve_location=requestData['location'], city__isnull=False, org__isnull=False, state__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').values('org', 'state').annotate(count=Sum('request_counter'))
                qs = qs.filter(reduce(lambda x, y: x | y, [Q(state=item) for item in filter_states]))
                # print('&&&&&&&&&&&&&&&&&&', qs.query)
                if qs:
                    n['asn'] = list(qs)
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['data'] = list(rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)


# class UpdateServeHistoryView(APIView):
#     def get(self,request):
#         response_data = {}
#         data = []
        
#         qs = ServeIpDetails.objects.filter(is_deleted=False, is_blocked=False).order_by('id')
#         print('&&&&&&&&&&&&&&&&&&', qs.query)
#         if qs:
#             for r in qs:
#                 print(r)
#                 mesurObj = ServeMeasurementHistory.objects.filter(serve_ip_details_id=r.id).update(address=r.address, country=r.country, state=r.state, city=r.city, postal=r.postal, latitude=r.latitude, longitude=r.latitude)
#             response_data['status'] = 1
#             response_data['message'] = 'Serve location found.'
#             response_data['data'] = []
#             return JsonResponse(response_data, status=200)
#         else:
#             response_data['status'] = 0
#             response_data['message'] = 'No record found in our database.'
#             response_data['data'] = []
#             return JsonResponse(response_data, status=200)


class TelephoneCircleServeLocationRoutingDetoreView(APIView):
    def get(self,request):
        response_data = {}
        data = []
        ### Telephone Circle Area Array ###
        zone_array = {
            'Mohali':['Punjab', 'Chandigarh'],
            'Guwahati':['Assam'],
            'Kolkata':['Kolkata'],
            'Mumbai':['Mumbai', 'New Mumbai', 'Maharashtra', 'Goa'],
            'Bengaluru':['Karnataka', 'Bengaluru']
        }
        q_load = {'month':TruncDay('created_date')}

        qs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False)
        qs = qs.filter(serve_location='Kolkata')
        qs = qs.filter(created_date__date__lte=datetime.datetime.today())
        qs = qs.filter(created_date__date__gte=datetime.datetime.today() - datetime.timedelta(days=7))
        # qs = qs.annotate(**q_load)
        qs = qs.exclude(serve_location ='localhost')
        qs = qs.exclude(serve_location ='Localhost')
        qs = qs.order_by('id')
        qs = qs.values('id', 'created_date')
        qs = qs.annotate(total_hit_count=Count('id'))
        
        #print('&&&&&&&&&&&&&&&&&&', qs.query)
        if qs:
            for l in qs:
                l['inside_zone_hit_count'] = 0
                l['outside_zone_hit_count'] = 0
                rs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, id=l['id'], country__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('city').values('city').annotate(count=Count('id'))
                if rs:
                    for key in zone_array:
                        if key == 'Kolkata':   
                            for s in rs:
                                if s['city'] in zone_array[key]:
                                    l['inside_zone_hit_count'] += s['count']
                                else:
                                    l['outside_zone_hit_count'] += s['count']
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['data'] = list(qs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        response_data = {}
        requestData = request.data
        data = []
        #print(requestData)
        if requestData['duration'] == 'yearly':
            q_load = {'month':TruncYear('created_date')}
            date_filter = {'created_date__lte':requestData['to_date'], 'created_date__gte':requestData['from_date']}

        if requestData['duration'] == 'monthly':
            q_load = {'month':TruncMonth('created_date')}
            date_filter = {'created_date__lte':requestData['to_date'], 'created_date__gte':requestData['from_date']}

        if requestData['duration'] == 'quaterly':
            q_load = {'month':TruncQuarter('created_date')}
            date_filter = {'created_date__lte':requestData['to_date'], 'created_date__gte':requestData['from_date']}

        if requestData['duration'] == 'weekly':
            q_load = {'month':TruncWeek('created_date')}
            date_filter = {'created_date__lte':requestData['to_date'], 'created_date__gte':requestData['from_date']}

        if requestData['duration'] == 'dayly':
            q_load = {'month':TruncDay('created_date')}
            date_filter = {'created_date__lte':requestData['to_date'], 'created_date__gte':requestData['from_date']}

        if requestData['duration'] == 'hourly':
            q_load = {'month':TruncHour('created_date')}
            date_filter = {'created_date__lte':requestData['to_date'], 'created_date__gte':requestData['from_date']}
        
        if requestData['duration'] == 'minute':
            q_load = {'month':TruncMinute('created_date')}
            date_filter = {'created_date__lte':requestData['to_date'], 'created_date__gte':requestData['from_date']}

        if requestData['duration'] == 'second':
            q_load = {'month':TruncSecond('created_date')}
            date_filter = {'created_date__lte':requestData['to_date'], 'created_date__gte':requestData['from_date']}
        ### Telephone Circle Area Array ###
        zone_array = {
            'Mohali':['Punjab', 'Chandigarh'],
            'Guwahati':['Assam'],
            'Kolkata':['Kolkata'],
            'Mumbai':['Mumbai', 'New Mumbai', 'Maharashtra', 'Goa'],
            'Bengaluru':['Karnataka', 'Bengaluru']
        }
        qs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, country__isnull=False)
        qs = qs.filter(serve_location=requestData['anycast_location'])
        qs = qs.filter(**date_filter)
        qs = qs.annotate(**q_load)
        qs = qs.exclude(serve_location ='localhost')
        qs = qs.exclude(serve_location ='Localhost')
        qs = qs.order_by('id')
        qs = qs.values('id', 'created_date')
        qs = qs.annotate(total_hit_count=Count('id'))
        #print('&&&&&&&&&&&&&&&&&&', qs.query)
        if qs:
            for l in qs:
                l['inside_zone_hit_count'] = 0
                l['outside_zone_hit_count'] = 0
                rs = ServeMeasurementHistory.objects.filter(is_deleted=False, is_blocked=False, serve_location__isnull=False, state__isnull=False, id=l['id'], country__isnull=False).exclude(serve_location ='localhost').exclude(serve_location ='Localhost').order_by('city').values('city').annotate(count=Count('id'))
                # print('&&&&&&&&&&&&&&&&&&888888888888888888', rs.query)
                if rs:
                    for key in zone_array:
                        if key == requestData['anycast_location']:   
                            # print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&', zone_array[key], '***** SERVE LOCATION', l['serve_location'])
                            for s in rs:
                                if s['city'] in zone_array[key]:
                                    l['inside_zone_hit_count'] += s['count']
                                    # print('State Have', s['state'], '***** SERVE LOCATION', l['serve_location'])
                                else:
                                    # print('State Have Not', s['state'], '***** Count', s['count'])
                                    l['outside_zone_hit_count'] += s['count']
                # data.append({l['serve_location']:list(rs)})
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['data'] = list(qs)
            # response_data['data'] = data
            # response_data['Zone'] = zone_array
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class AnycastServerLocationView(APIView):
    def get(self,request):
        response_data = {}
        data = []
        anycast_rs = ServeIpDetails.objects.filter(is_blocked=False, is_deleted=False)
        anycast_rs = anycast_rs.filter(serve_location__isnull=False, state__isnull=False, country__isnull=False)
        anycast_rs = anycast_rs.exclude(serve_location ='localhost')
        anycast_rs = anycast_rs.exclude(serve_location ='Localhost')
        anycast_rs = anycast_rs.order_by('serve_location')
        anycast_rs = anycast_rs.values('id', 'serve_location')
        anycast_rs = anycast_rs.distinct('serve_location')

        #print('&&&&&&&&&&&&&&&&&&', anycast_rs.query)
        if anycast_rs:
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['anycast_servers'] = list(anycast_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class RootServerListView(APIView):
    def get(self,request):
        response_data = {}
        data = []
        rootserver_rs = RootServers.objects.filter(is_blocked=False, is_deleted=False)
        rootserver_rs = rootserver_rs.order_by('id')
        rootserver_rs = rootserver_rs.values('id', 'server_name', 'display_name')
        if rootserver_rs:
            response_data['status'] = 1
            response_data['message'] = 'Server list found.'
            response_data['root_servers'] = list(rootserver_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class RootServerStateWiseLatencyView(APIView):
    def get(self,request):
        response_data = {}
        today = datetime.datetime.now()
        # RootServerPinResultUpdateCornView()

        # rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, query_type='ping')
        # rootserverhistory_rs = rootserverhistory_rs.values('register_anchor_state', 'created_date')
        # rootserverhistory_rs = rootserverhistory_rs.order_by('-id')[:2]

        rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, query_type='ping', created_date__date=today, execution_status='success').exclude(rtt_avg=0)
        rootserverhistory_rs = rootserverhistory_rs.order_by('register_anchor_state')
        rootserverhistory_rs = rootserverhistory_rs.values('register_anchor_state')
        rootserverhistory_rs = rootserverhistory_rs.annotate(avg_latency=Avg('rtt_avg'))
        rootserverhistory_rs = [{'name': x['register_anchor_state'], 'value': x['avg_latency']} for x in rootserverhistory_rs]
        if rootserverhistory_rs:
            response_data['status'] = 1
            response_data['message'] = 'Latency record found.'
            response_data['root_servers'] = list(rootserverhistory_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)
    def post(self,request):
        response_data = {}
        requestData = request.data
        today = datetime.datetime.now()
        d = datetime.datetime.utcnow()
        #print(requestData)
        #print(today)
        d.hour
        if d.hour <= 12:
            time_threshold = timezone.now() - timedelta(hours=12)
            print("Run your code here")
            # nothing happens, it's after 9:00 here.


        
        rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, register_anchor_state__isnull=False, query_type='ping', created_date__date=requestData['filter_date'], execution_status='success')
        if requestData['latency_type'] == 'rtt_avg':
            rootserverhistory_rs = rootserverhistory_rs.exclude(rtt_avg=0)

        if requestData['latency_type'] == 'rtt_min':
            rootserverhistory_rs = rootserverhistory_rs.exclude(rtt_min=0)

        if requestData['latency_type'] == 'rtt_max':
            rootserverhistory_rs = rootserverhistory_rs.exclude(rtt_max=0)
            
        if len(requestData['rootserverids']) > 0:
            rootserverhistory_rs = rootserverhistory_rs.filter(root_server_id__in=requestData['rootserverids'])
        # if len(requestData['anchor_states']) > 0:
        #     rootserverhistory_rs = rootserverhistory_rs.filter(register_anchor_state__in=requestData['anchor_states'])
        rootserverhistory_rs = rootserverhistory_rs.order_by('register_anchor_state')
        rootserverhistory_rs = rootserverhistory_rs.values('register_anchor_state')
        rootserverhistory_rs = rootserverhistory_rs.annotate(avg_latency=Avg(requestData['latency_type']))
        rootserverhistory_rs = [{'name': x['register_anchor_state'], 'value': x['avg_latency']} for x in rootserverhistory_rs]
        if rootserverhistory_rs:
            response_data['status'] = 1
            response_data['message'] = 'Latency record found.'
            response_data['root_servers'] = list(rootserverhistory_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class RootServerStatesAndLocationsView(APIView):
    def get(self,request):
        response_data = {}
        today = datetime.datetime.now()
        rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, query_type='ping', register_anchor_state__isnull=False, created_date__date=today, execution_status='success')
        rootserverhistory_rs = rootserverhistory_rs.exclude(register_anchor_state="")
        rootserverhistory_rs = rootserverhistory_rs.order_by('register_anchor_state')
        rootserverhistory_rs = rootserverhistory_rs.values('register_anchor_state')
        # rootserverhistory_rs = rootserverhistory_rs.annotate(count=Count('register_anchor_state'))
        rootserverhistory_rs = rootserverhistory_rs.distinct('register_anchor_state')
        if rootserverhistory_rs:
            for s in rootserverhistory_rs:
                location_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, query_type='ping', register_anchor_state__isnull=False, created_date__date=today, execution_status='success', register_anchor_state=s['register_anchor_state'])
                location_rs = location_rs.exclude(register_anchor_location="")
                location_rs = location_rs.order_by('register_anchor_location')
                location_rs = location_rs.values('register_anchor_location')
                # rootserverhistory_rs = rootserverhistory_rs.annotate(count=Count('register_anchor_state'))
                location_rs = location_rs.distinct('register_anchor_location')
                if location_rs:
                    s['locations'] = list(location_rs)
                else:
                    s['locations'] = []
            response_data['status'] = 1
            response_data['message'] = 'Latency record found.'
            response_data['root_servers'] = list(rootserverhistory_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)
    def post(self,request):
        response_data = {}
        requestData = request.data
        today = datetime.datetime.now()
        d = datetime.datetime.utcnow()
        #print(requestData)
        #print(today)
        d.hour
        if d.hour <= 12:
            time_threshold = timezone.now() - timedelta(hours=12)
            print("Run your code here")
            # nothing happens, it's after 9:00 here.


        
        rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, register_anchor_state__isnull=False, query_type='ping', created_date__date=requestData['filter_date'])
        if len(requestData['rootserverids']) > 0:
            rootserverhistory_rs = rootserverhistory_rs.filter(root_server_id__in=requestData['rootserverids'])
        # if len(requestData['anchor_states']) > 0:
        #     rootserverhistory_rs = rootserverhistory_rs.filter(register_anchor_state__in=requestData['anchor_states'])
        rootserverhistory_rs = rootserverhistory_rs.order_by('register_anchor_state')
        rootserverhistory_rs = rootserverhistory_rs.values('register_anchor_state')
        rootserverhistory_rs = rootserverhistory_rs.annotate(avg_latency=Avg(requestData['latency_type']))
        rootserverhistory_rs = [{'name': x['register_anchor_state'], 'value': x['avg_latency']} for x in rootserverhistory_rs]
        if rootserverhistory_rs:
            response_data['status'] = 1
            response_data['message'] = 'Latency record found.'
            response_data['root_servers'] = list(rootserverhistory_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)


class RootServerSoaRecordsView(APIView):
    def get(self,request):
        response_data = {}
        today = datetime.datetime.now()
        rootserversoahistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, query_type='soa', created_date__date=today)
        rootserversoahistory_rs = rootserversoahistory_rs.order_by('register_anchor_location')
        rootserversoahistory_rs = rootserversoahistory_rs.values('id', 'anchor_id__anchor_name', 'register_anchor_state', 'register_anchor_location', 'soa_record')
        if rootserversoahistory_rs:
            response_data['status'] = 1
            response_data['message'] = 'Soa record found.'
            response_data['root_servers'] = list(rootserversoahistory_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self,request):
        response_data = {}
        requestData = request.data
        today = datetime.datetime.now()
        d = datetime.datetime.utcnow()
        print(requestData['filter_date'])
        print(today)
        d.hour
        if d.hour <= 12:
            time_threshold = timezone.now() - timedelta(hours=12)
            print("Run your code here")
            # nothing happens, it's after 9:00 here.



        rootserversoahistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, query_type='soa', created_date__date=requestData['filter_date'])
        rootserversoahistory_rs = rootserversoahistory_rs.order_by('register_anchor_state')
        rootserversoahistory_rs = rootserversoahistory_rs.values('id', 'anchor_id__anchor_name', 'register_anchor_state', 'register_anchor_location', 'soa_record')
        if rootserverhistory_rs:
            response_data['status'] = 1
            response_data['message'] = 'Latency record found.'
            response_data['root_servers'] = list(rootserverhistory_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

# def root_server_pin_execution(data):
#     bulk_insert_record_set = []
#     # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
#     set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
#     # print('executed_measurement', latency_check_history_id)
#     # print(rs.query)
#     if len(data) > 0:
#         for n in data:
#             # print('######## Server URL #########', n['rd3mn_server_url'])
#             # url = str(settings.AIORI_ANCHOR_HOST) + str(settings.AIORI_ANCHOR_URL) + "ping/?lease_id=" + anchor['lease_id']
#             url = str(n['rd3mn_server_url']) + "ping/?lease_id=" + n['lease_id']
#             # print('&&&&&&&&&&&&&&', url)
#             querydata = {
#                     "cmd_value": "ping",
#                     "cmd_type": "regular",
#                     "run_count": "3",
#                     "region": n['region'].lower(),
#                     "hosts": n['hosts'],
#                     "anchors": n['anchors']
#                     }
#             # print('&&&&&------&&&&&&&', querydata)
#             result = requests.post(url, json=querydata, headers=set_headers)
#             # print('&&&&&&&&&&&&&&  json_result  &&&&&&&&&&&&&&&&&&&&&&&&&',result.json())
#             if result.status_code == 200:
#                 json_result = result.json()
#                 # print('&&&&&&&&&&&&&&  json_result  &&&&&&&&&&&&&&&&&&&&&&&&&',json_result)
#                 ########### Create Record Set #########
#                 bulk_insert_record_set.append(RootServerLatencyCheckHistoryDetails(
#                 root_server_id=n['root_server_id'],
#                 anchor_id=n['anchor_id'],
#                 user_anchor_id=n['user_anchor_id'],
#                 anchor_user_id=n['anchor_user_id'],
#                 commend_request_payload= querydata,
#                 register_anchor_state=n['register_anchor_state'],
#                 register_anchor_location = n['register_anchor_location'].lower(),
#                 commend_query_id=json_result['id'],
#                 created_date=timezone.now(),
#                 modified_date=timezone.now()
#             ))
#                 print(json_result['id'])
#             else:
#                 print(result.status_code)
#                 result
#                 bulk_insert_record_set.append(RootServerLatencyCheckHistoryDetails(
#                 root_server_id=n['root_server_id'],
#                 anchor_id=n['anchor_id'],
#                 user_anchor_id=n['user_anchor_id'],
#                 anchor_user_id=n['anchor_user_id'],
#                 commend_request_payload= querydata,
#                 register_anchor_state=n['register_anchor_state'],
#                 register_anchor_location = n['register_anchor_location'].lower(),
#                 created_date=timezone.now(),
#                 modified_date=timezone.now()
#             ))
#         #print('###################### bulk_insert_record_set #################', bulk_insert_record_set)
#         msg = RootServerLatencyCheckHistoryDetails.objects.bulk_create(bulk_insert_record_set)
def root_server_pin_execution(
    data,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_workers: int = DEFAULT_MAX_WORKERS,
    request_timeout: int = DEFAULT_TIMEOUT,
):
    start_ts = datetime.datetime.now()
    total_requests = len(data)
    print(f"[INFO] root_server_pin_execution started with {total_requests} records")

    if total_requests == 0:
        print("[INFO] No data to process. Exiting.")
        return

    # Shared requests session with retry/backoff
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=max_workers)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    headers = {"content-type": "application/json", "apikey": API_KEY}

    # Worker function for HTTP requests
    def _task(n: dict):
        url = f"{n['rd3mn_server_url']}ping/?lease_id={n['lease_id']}"
        payload = {
            "cmd_value": "ping",
            "cmd_type": "regular",
            "run_count": "3",
            "region": n["region"].lower(),
            "hosts": n["hosts"],
            "anchors": n["anchors"],
        }
        try:
            resp = session.post(url, json=payload, headers=headers, timeout=request_timeout)
            commend_query_id = resp.json().get("id") if resp.ok else None
            if not resp.ok:
                print(f"[WARN] Non-200 response {resp.status_code} for URL: {url}")
        except Exception as e:
            commend_query_id = None
            print(f"[WARN] Request failed for {url}: {e}")

        return {
            "root_server_id": n["root_server_id"],
            "anchor_id": n["anchor_id"],
            "user_anchor_id": n["user_anchor_id"],
            "anchor_user_id": n["anchor_user_id"],
            "commend_request_payload": payload,
            "register_anchor_state": n["register_anchor_state"],
            "register_anchor_location": n["register_anchor_location"].lower(),
            "commend_query_id": commend_query_id,
            "created_date": timezone.now(),
            "modified_date": timezone.now(),
        }

    batch_dicts = []
    inserted_total = 0
    processed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_task, n) for n in data]

        for fut in as_completed(futures):
            res = fut.result()
            if res:
                batch_dicts.append(res)
            processed_count += 1

            # Progress logging
            if processed_count % LOG_PROGRESS_EVERY == 0:
                print(f"[INFO] Processed {processed_count}/{total_requests} requests")

            # Insert in batches
            if len(batch_dicts) >= batch_size:
                objs = [
                    RootServerLatencyCheckHistoryDetails(
                        root_server_id=d["root_server_id"],
                        anchor_id=d["anchor_id"],
                        user_anchor_id=d["user_anchor_id"],
                        anchor_user_id=d["anchor_user_id"],
                        commend_request_payload=d["commend_request_payload"],
                        register_anchor_state=d["register_anchor_state"],
                        register_anchor_location=d["register_anchor_location"],
                        commend_query_id=d["commend_query_id"],
                        created_date=d["created_date"],
                        modified_date=d["modified_date"],
                    )
                    for d in batch_dicts
                ]
                RootServerLatencyCheckHistoryDetails.objects.bulk_create(objs, ignore_conflicts=True)
                inserted_total += len(objs)
                print(f"[INFO] Inserted batch of {len(objs)} rows. Total inserted: {inserted_total}")
                batch_dicts.clear()

    # Final remaining inserts
    if batch_dicts:
        objs = [
            RootServerLatencyCheckHistoryDetails(
                root_server_id=d["root_server_id"],
                anchor_id=d["anchor_id"],
                user_anchor_id=d["user_anchor_id"],
                anchor_user_id=d["anchor_user_id"],
                commend_request_payload=d["commend_request_payload"],
                register_anchor_state=d["register_anchor_state"],
                register_anchor_location=d["register_anchor_location"],
                commend_query_id=d["commend_query_id"],
                created_date=d["created_date"],
                modified_date=d["modified_date"],
            )
            for d in batch_dicts
        ]
        RootServerLatencyCheckHistoryDetails.objects.bulk_create(objs, ignore_conflicts=True)
        inserted_total += len(objs)
        print(f"[INFO] Inserted final batch of {len(objs)} rows. Total inserted: {inserted_total}")

    session.close()
    elapsed = datetime.datetime.now() - start_ts
    print(f"[INFO] root_server_pin_execution finished. Total inserted: {inserted_total}. Took {elapsed.total_seconds():.2f}s")


def root_server_dns_soa_execution(data):
    bulk_insert_record_set = []
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    # print('executed_measurement', latency_check_history_id)
    # print(rs.query)
    if len(data) > 0:
        for n in data:
            # print('######## Server URL #########', n['rd3mn_server_url'])
            # url = str(settings.AIORI_ANCHOR_HOST) + str(settings.AIORI_ANCHOR_URL) + "ping/?lease_id=" + anchor['lease_id']
            url = str(n['rd3mn_server_url']) + "dnsq/soa/?lease_id=" + n['lease_id']
            # print('&&&&&&&&&&&&&&', url)
            querydata = {
                    "name": str(n['server_name']),
                    "anchors": n['anchors']
                    }   
            # print('&&&&&------&&&&&&&', querydata)
            result = requests.post(url, json=querydata, headers=set_headers)
            # print('&&&&&&&&&&&&&&  json_result  &&&&&&&&&&&&&&&&&&&&&&&&&',result.json())
            if result.status_code == 200:
                json_result = result.json()
                # print('&&&&&&&&&&&&&&  json_result  &&&&&&&&&&&&&&&&&&&&&&&&&',json_result)
                ########### Create Record Set #########
                bulk_insert_record_set.append(RootServerLatencyCheckHistoryDetails(
                root_server_id=n['root_server_id'],
                anchor_id=n['anchor_id'],
                user_anchor_id=n['user_anchor_id'],
                anchor_user_id=n['anchor_user_id'],
                commend_request_payload= querydata,
                register_anchor_state=n['register_anchor_state'],
                register_anchor_location = n['register_anchor_location'].lower(),
                commend_query_id=json_result['id'],
                query_type='soa',
                created_date=timezone.now(),
                modified_date=timezone.now()
            ))
                print(json_result['id'])
            else:
                print(result.status_code)
                result
                bulk_insert_record_set.append(RootServerLatencyCheckHistoryDetails(
                root_server_id=n['root_server_id'],
                anchor_id=n['anchor_id'],
                user_anchor_id=n['user_anchor_id'],
                anchor_user_id=n['anchor_user_id'],
                commend_request_payload= querydata,
                register_anchor_state=n['register_anchor_state'],
                register_anchor_location = n['register_anchor_location'].lower(),
                query_type='soa',
                created_date=timezone.now(),
                modified_date=timezone.now()
            ))
        #print('###################### bulk_insert_record_set #################', bulk_insert_record_set)
        msg = RootServerLatencyCheckHistoryDetails.objects.bulk_create(bulk_insert_record_set)

# def RD3MNPinCommandExecutionForRootServerCornView():
#     data = []
#     bulk_insert_record_set = []
#     rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active", location_register_status="registered", anchor_id__is_online=True, anchor_id__version=1)
#     rs = rs.exclude(anchor_id__anchor_name ='nats-blr-anchor')
#     rs = rs.exclude(anchor_id__anchor_name ='nats-gwh-anchor')
#     rs = rs.exclude(anchor_id__anchor_name ='nats-kol-anchor')
#     rs = rs.exclude(anchor_id__anchor_name ='nats-moh-anchor')
#     rs = rs.exclude(anchor_id__anchor_name ='nats-mum-anchor')
#     rs = rs.values('id', 'anchor_id__anchor_name', 'lease_id', 'aiori_anchor_id', 'anchor_id__server_url', 'anchor_id', 'administrative_area_level_1', 'location', 'user_id')
#     rs = rs.order_by('-id')
#
#     rootserver_rs = RootServers.objects.filter(is_blocked=False, is_deleted=False)
#     rootserver_rs = rootserver_rs.values('id', 'server_name', 'server_ip_v4', 'server_ip_v6')
#     if rootserver_rs:
#         if rs:
#             for r in rootserver_rs:
#                 for anchor in rs:
#                     querydata = {
#                     "cmd_value": "ping",
#                     "cmd_type": "regular",
#                     "run_count": "3",
#                     "region": anchor['location'].lower(),
#                     "hosts": [r['server_ip_v4']],
#                     "anchors": [anchor['aiori_anchor_id']],
#                     "lease_id": anchor['lease_id'],
#                     "root_server_id":r['id'],
#                     "anchor_id": anchor['anchor_id'],
#                     "user_anchor_id": anchor['id'],
#                     "anchor_user_id": anchor['user_id'],
#                     "register_anchor_state": anchor['administrative_area_level_1'],
#                     "register_anchor_location": anchor['location'],
#                     "rd3mn_server_url": anchor['anchor_id__server_url']
#                     }
#                     data.append(querydata)
#             if len(data) > 0:
#                 root_server_pin_execution(data)
                # root_server_dns_soa_execution(data)
def RD3MNPinCommandExecutionForRootServerCornView():
    data = []

    # Pre-filter anchors in a single query
    excluded_names = [
        'nats-blr-anchor', 'nats-gwh-anchor', 'nats-kol-anchor',
        'nats-moh-anchor', 'nats-mum-anchor'
    ]

    anchors = (
        UserAnchor.objects.filter(
            is_deleted=False,
            is_blocked=False,
            status="active",
            location_register_status="registered",
            anchor_id__is_online=True,
            anchor_id__version=1
        )
        .exclude(anchor_id__anchor_name__in=excluded_names)
        .values(
            'id', 'anchor_id__anchor_name', 'lease_id', 'aiori_anchor_id',
            'anchor_id__server_url', 'anchor_id', 'administrative_area_level_1',
            'location', 'user_id'
        )
        .order_by('-id')
    )

    root_servers = RootServers.objects.filter(
        is_blocked=False, is_deleted=False
    ).values('id', 'server_name', 'server_ip_v4', 'server_ip_v6')

    # Build data efficiently
    for anchor in anchors.iterator():
        location = anchor['location'].lower()
        for root in root_servers.iterator():
            data.append({
                "cmd_value": "ping",
                "cmd_type": "regular",
                "run_count": "3",
                "region": location,
                "hosts": [root['server_ip_v4']],
                "anchors": [anchor['aiori_anchor_id']],
                "lease_id": anchor['lease_id'],
                "root_server_id": root['id'],
                "anchor_id": anchor['anchor_id'],
                "user_anchor_id": anchor['id'],
                "anchor_user_id": anchor['user_id'],
                "register_anchor_state": anchor['administrative_area_level_1'],
                "register_anchor_location": anchor['location'],
                "rd3mn_server_url": anchor['anchor_id__server_url']
            })

    if data:
        print(f"[INFO] Sending {len(data)} ping requests...")
        root_server_pin_execution(data)
    else:
        print("[INFO] No data to process.")

class RootServerView(APIView):
    # def get(self,request):
    #     response_data = {}
    #     data = []
    #     bulk_insert_record_set = []
    #     rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active", location_register_status="registered", anchor_id__is_online=True, anchor_id__version=1)
    #     rs = rs.exclude(anchor_id__anchor_name ='nats-blr-anchor')
    #     rs = rs.exclude(anchor_id__anchor_name ='nats-gwh-anchor')
    #     rs = rs.exclude(anchor_id__anchor_name ='nats-kol-anchor')
    #     rs = rs.exclude(anchor_id__anchor_name ='nats-moh-anchor')
    #     rs = rs.exclude(anchor_id__anchor_name ='nats-mum-anchor')
    #     rs = rs.values('id', 'anchor_id__anchor_name', 'lease_id', 'aiori_anchor_id', 'anchor_id__server_url', 'anchor_id', 'administrative_area_level_1', 'location', 'user_id')
    #     rs = rs.order_by('-id')
    #
    #     rootserver_rs = RootServers.objects.filter(is_blocked=False, is_deleted=False)
    #     rootserver_rs = rootserver_rs.values('id', 'server_name', 'server_ip_v4', 'server_ip_v6')
    #     if rootserver_rs:
    #         if rs:
    #             for r in rootserver_rs:
    #                 for anchor in rs:
    #                     querydata = {
    #                     "cmd_value": "ping",
    #                     "cmd_type": "regular",
    #                     "run_count": "3",
    #                     "region": anchor['location'].lower(),
    #                     "server_name": r['server_name'],
    #                     "hosts": [r['server_ip_v4']],
    #                     "anchors": [anchor['aiori_anchor_id']],
    #                     "lease_id": anchor['lease_id'],
    #                     "root_server_id":r['id'],
    #                     "anchor_id": anchor['anchor_id'],
    #                     "user_anchor_id": anchor['id'],
    #                     "anchor_user_id": anchor['user_id'],
    #                     "register_anchor_state": anchor['administrative_area_level_1'],
    #                     "register_anchor_location": anchor['location'],
    #                     "rd3mn_server_url": anchor['anchor_id__server_url']
    #                     }
    #                     data.append(querydata)
    #             if len(data) > 0:
    #                 root_server_pin_execution(data)
    #                 # root_server_dns_soa_execution(data)
    #         response_data['status'] = 1
    #         response_data['message'] = 'Serve location found.'
    #         response_data['root_servers'] = list(rootserver_rs)
    #         response_data['anchors'] = list(rs)
    #         response_data['fire_data'] = data
    #         return JsonResponse(response_data, status=200)
    #     else:
    #         response_data['status'] = 0
    #         response_data['message'] = 'No record found in our database.'
    #         response_data['data'] = []
    #         return JsonResponse(response_data, status=200)
    def get(self, request):
        response_data = {}

        data = []

        # Pre-filter anchors in a single query
        excluded_names = [
            'nats-blr-anchor', 'nats-gwh-anchor', 'nats-kol-anchor',
            'nats-moh-anchor', 'nats-mum-anchor'
        ]

        anchors = (
            UserAnchor.objects.filter(
                is_deleted=False,
                is_blocked=False,
                status="active",
                location_register_status="registered",
                anchor_id__is_online=True,
                anchor_id__version=1
            )
            .exclude(anchor_id__anchor_name__in=excluded_names)
            .values(
                'id', 'anchor_id__anchor_name', 'lease_id', 'aiori_anchor_id',
                'anchor_id__server_url', 'anchor_id', 'administrative_area_level_1',
                'location', 'user_id'
            )
            .order_by('-id')
        )

        root_servers = RootServers.objects.filter(
            is_blocked=False, is_deleted=False
        ).values('id', 'server_name', 'server_ip_v4', 'server_ip_v6')

        # Build data efficiently
        for anchor in anchors.iterator():
            location = anchor['location'].lower()
            for root in root_servers.iterator():
                data.append({
                    "cmd_value": "ping",
                    "cmd_type": "regular",
                    "run_count": "3",
                    "region": location,
                    "hosts": [root['server_ip_v4']],
                    "anchors": [anchor['aiori_anchor_id']],
                    "lease_id": anchor['lease_id'],
                    "root_server_id": root['id'],
                    "anchor_id": anchor['anchor_id'],
                    "user_anchor_id": anchor['id'],
                    "anchor_user_id": anchor['user_id'],
                    "register_anchor_state": anchor['administrative_area_level_1'],
                    "register_anchor_location": anchor['location'],
                    "rd3mn_server_url": anchor['anchor_id__server_url']
                })

        if data:
            print(f"[INFO] Sending {len(data)} ping requests...")
            root_server_pin_execution(data)
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['root_servers'] = list(root_servers)
            response_data['anchors'] = list(anchors)
            response_data['fire_data'] = data
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['root_servers'] = []
            response_data['anchors'] = []
            response_data['fire_data'] = []

        return JsonResponse(response_data, status=200)


# def RootServerPinResultUpdateCornView():
#     today = datetime.datetime.now()
#     bulk_update_record_set = []
#     rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, execution_status='running', commend_query_id__isnull=False, query_type='ping', created_date__date=today)
#     rootserverhistory_rs = rootserverhistory_rs.values('id', 'commend_query_id', 'anchor_id__db_url', 'anchor_id__storage_db')
#     if rootserverhistory_rs:
#         for x in rootserverhistory_rs:
#             #print(x)
#             query = str(x['anchor_id__db_url']) + "/query?pretty=true&db=" + str(x['anchor_id__storage_db']) + "&q=SELECT rtt_avg, rtt_max, rtt_min FROM ping WHERE id='" + x['commend_query_id'] + "'"
#             result = requests.get(query)
#             if result.status_code == 200:
#                 json_result = result.json()
#                 # print('&&&&&&&&& json_result &&&&&&&&&&', json_result)
#                 for val in json_result['results']:
#                     if "series" in val:
#                         for ser in val['series']:
#                             if "values" in ser:
#                                 for value in ser['values']:
#                                     #print('&&&&&&&&& json_result &&&&&&&&&&',value)
#                                     bulk_update_record_set.append(RootServerLatencyCheckHistoryDetails(
#                                         pk=x['id'],
#                                         time=value[0],
#                                         rtt_avg=value[1],
#                                         rtt_max=value[2],
#                                         rtt_min=value[3],
#                                         execution_status='success'
#                                     ))
#         RootServerLatencyCheckHistoryDetails.objects.bulk_update(bulk_update_record_set, ['time', 'rtt_avg', 'rtt_max', 'rtt_min', 'execution_status'])
def RootServerPinResultUpdateCornView(batch_size=1000):
    today = datetime.datetime.now()
    print(f"[INFO] RootServerPinResultUpdateCornView started at {timezone.now()}")

    qs = RootServerLatencyCheckHistoryDetails.objects.filter(
        is_blocked=False,
        is_deleted=False,
        execution_status='running',
        commend_query_id__isnull=False,
        query_type='ping',
        created_date__date=today
    ).values('id', 'commend_query_id', 'anchor_id__db_url', 'anchor_id__storage_db')

    total_count = qs.count()
    if total_count == 0:
        print(f"[INFO] No records found to update at {timezone.now()}")
        print(f"[INFO] RootServerPinResultUpdateCornView finished at {timezone.now()}")
        return

    print(f"[INFO] Found {total_count} records to update")
    bulk_update_record_set = []
    processed_count = 0

    for x in qs.iterator():  # stream results to avoid memory spikes
        query = (
            f"{x['anchor_id__db_url']}/query?pretty=true&db={x['anchor_id__storage_db']}"
            f"&q=SELECT rtt_avg, rtt_max, rtt_min FROM ping WHERE id='{x['commend_query_id']}'"
        )
        print(f"[DEBUG] Processing record id={x['id']} with query_id={x['commend_query_id']}")

        try:
            result = requests.get(query, timeout=10)
            if result.status_code == 200:
                json_result = result.json()
                for val in json_result.get('results', []):
                    if "series" in val:
                        for ser in val['series']:
                            for value in ser.get('values', []):
                                bulk_update_record_set.append(
                                    RootServerLatencyCheckHistoryDetails(
                                        pk=x['id'],
                                        time=value[0],
                                        rtt_avg=value[1],
                                        rtt_max=value[2],
                                        rtt_min=value[3],
                                        execution_status='success',
                                    )
                                )
        except Exception as e:
            print(f"[ERROR] Failed query for id={x['id']} url={query}, error={e}")

        # Bulk update in chunks
        if len(bulk_update_record_set) >= batch_size:
            RootServerLatencyCheckHistoryDetails.objects.bulk_update(
                bulk_update_record_set, ['time', 'rtt_avg', 'rtt_max', 'rtt_min', 'execution_status']
            )
            processed_count += len(bulk_update_record_set)
            print(f"[INFO] Updated batch of {len(bulk_update_record_set)} rows. Total updated: {processed_count}")
            bulk_update_record_set.clear()

    # Final remaining updates
    if bulk_update_record_set:
        RootServerLatencyCheckHistoryDetails.objects.bulk_update(
            bulk_update_record_set, ['time', 'rtt_avg', 'rtt_max', 'rtt_min', 'execution_status']
        )
        processed_count += len(bulk_update_record_set)
        print(f"[INFO] Updated final batch of {len(bulk_update_record_set)} rows. Total updated: {processed_count}")

    print(f"[INFO] RootServerPinResultUpdateCornView finished at {timezone.now()}")

class RootServerPinResultUpdateView(APIView):
    def get(self,request):
        today = datetime.datetime.now()
        response_data = {}
        bulk_update_record_set = []
        rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, execution_status='running', commend_query_id__isnull=False, query_type='ping', created_date__date=today)
        rootserverhistory_rs = rootserverhistory_rs.values('id', 'commend_query_id', 'anchor_id__db_url', 'anchor_id__storage_db')
        if rootserverhistory_rs:
            for x in rootserverhistory_rs:
                #print(x)
                query = str(x['anchor_id__db_url']) + "/query?pretty=true&db=" + str(x['anchor_id__storage_db']) + "&q=SELECT rtt_avg, rtt_max, rtt_min FROM ping WHERE id='" + x['commend_query_id'] + "'"
                result = requests.get(query)
                if result.status_code == 200:
                    json_result = result.json()
                    # print('&&&&&&&&& json_result &&&&&&&&&&', json_result)
                    for val in json_result['results']:
                        if "series" in val:
                            for ser in val['series']:
                                if "values" in ser:
                                    for value in ser['values']:
                                        #print('&&&&&&&&& json_result &&&&&&&&&&',value)
                                        bulk_update_record_set.append(RootServerLatencyCheckHistoryDetails(
                                            pk=x['id'],
                                            time=value[0],
                                            rtt_avg=value[1],
                                            rtt_max=value[2], 
                                            rtt_min=value[3], 
                                            execution_status='success'
                                        ))
            RootServerLatencyCheckHistoryDetails.objects.bulk_update(bulk_update_record_set, ['time', 'rtt_avg', 'rtt_max', 'rtt_min', 'execution_status']) 
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['root_servers_history'] = list(rootserverhistory_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

def RootServerSoaResultUpdateCornView():
    bulk_update_record_set = []
    # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
    set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
    rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, execution_status='running', commend_query_id__isnull=False, query_type='soa')
    rootserverhistory_rs = rootserverhistory_rs.values('id', 'commend_query_id', 'anchor_id__server_url')
    if rootserverhistory_rs:
        for x in rootserverhistory_rs:
            #print(x)
            query = str(x['anchor_id__server_url']) + "dnsq/soa/data/" + x['commend_query_id']
            #print('&&&&&&&&& query &&&&&&&&&&', query)
            result = requests.get(query, headers=set_headers)
            #print('&&&&&&&&& json_result &&&&&&&&&&', result)
            if result.status_code == 200:
                json_result = result.json()
                #print('&&&&&&&&& json_result &&&&&&&&&&', json_result)
                # bulk_update_record_set.append(json_result)
                bulk_update_record_set.append(RootServerLatencyCheckHistoryDetails(
                                        pk=x['id'],
                                        time=timezone.now(),
                                        soa_record=json_result,
                                        execution_status='success'
                                    ))
                                    
        RootServerLatencyCheckHistoryDetails.objects.bulk_update(bulk_update_record_set, ['time', 'soa_record', 'execution_status']) 

class RootServerSoaResultUpdateView(APIView):
    def get(self,request):
        response_data = {}
        bulk_update_record_set = []
        # set_headers = {"content-type": "application/json","X-IIFON-API-KEY": "87b068d2-0437-4d0b-9b41-8d09796db75e"}
        set_headers = {"content-type": "application/json","apikey": "996b6ecf6cdd0df6aa5ffeffaca6983b"}
        rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, execution_status='running', commend_query_id__isnull=False, query_type='soa')
        rootserverhistory_rs = rootserverhistory_rs.values('id', 'commend_query_id', 'anchor_id__server_url')
        if rootserverhistory_rs:
            for x in rootserverhistory_rs:
                #print(x)
                query = str(x['anchor_id__server_url']) + "dnsq/soa/data/" + x['commend_query_id']
                #print('&&&&&&&&& query &&&&&&&&&&', query)
                result = requests.get(query, headers=set_headers)
                #print('&&&&&&&&& json_result &&&&&&&&&&', result)
                if result.status_code == 200:
                    json_result = result.json()
                    #print('&&&&&&&&& json_result &&&&&&&&&&', json_result)
                    # bulk_update_record_set.append(json_result)
                    bulk_update_record_set.append(RootServerLatencyCheckHistoryDetails(
                                            pk=x['id'],
                                            time=timezone.now(),
                                            soa_record=json_result,
                                            execution_status='success'
                                        ))
                                        
            RootServerLatencyCheckHistoryDetails.objects.bulk_update(bulk_update_record_set, ['time', 'soa_record', 'execution_status']) 
            response_data['status'] = 1
            response_data['message'] = 'Serve location found.'
            response_data['root_servers_history'] = list(rootserverhistory_rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)
            
class RootServerStateWiseLatencyDownloadView(APIView):
    def get(self, request, form_date, to_date, rootserver_name):
        import xlwt
        import csv
        # from django.db.models.query import QuerySet, ValuesQuerySet
        from django.http import FileResponse
        from rest_framework import viewsets, renderers
        from rest_framework.decorators import action
        import tempfile
        response_data = {}
        # print('*********************', request.GET.get('form_date'))
        filter_form_date = form_date
        filter_to_date = to_date
        filter_rootserver_name = rootserver_name

        ### Export Data From DB in XLXE Format
        # response = HttpResponse(content_type='application/ms-excel')
        # response['Content-Disposition'] = 'attachment; filename="'+ filter_rootserver_name +'.xlsx"'

        # wb = xlwt.Workbook(encoding='utf-8')
        # ws = wb.add_sheet(filter_rootserver_name)

        # # Sheet header, first row
        # row_num = 0

        # font_style = xlwt.XFStyle()
        # font_style.font.bold = True

        # columns = ['Date', 'Location', 'RTT MAX', 'RTT AVG', 'RTT MIN',]

        # for col_num in range(len(columns)):
        #     ws.write(row_num, col_num, columns[col_num], font_style)

        # # Sheet body, remaining rows
        # font_style = xlwt.XFStyle()

        # rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, register_anchor_state__isnull=False, query_type='ping', created_date__date__gte=filter_form_date, created_date__date__lte=filter_to_date)
        # rootserverhistory_rs = rootserverhistory_rs.filter(root_server_id__display_name=filter_rootserver_name)
        # rootserverhistory_rs = rootserverhistory_rs.order_by('created_date')
        # rootserverhistory_rs = rootserverhistory_rs.values_list('created_date__date', 'register_anchor_location', 'rtt_max', 'rtt_avg', 'rtt_min')

        # # rows = User.objects.all().values_list('username', 'first_name', 'last_name', 'email')
        # for row in rootserverhistory_rs:
        #     row_num += 1
        #     for col_num in range(len(row)):
        #         ws.write(row_num, col_num, str(row[col_num]), font_style)

        # wb.save(response)

        ### Export Data From DB in CSV Format
        header = ['Date', 'Location', 'RTT MAX', 'RTT AVG', 'RTT MIN']

        ## Get Data From DB
        rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, register_anchor_state__isnull=False, query_type='ping', created_date__date__gte=filter_form_date, created_date__date__lte=filter_to_date)
        rootserverhistory_rs = rootserverhistory_rs.filter(root_server_id__display_name=filter_rootserver_name)
        rootserverhistory_rs = rootserverhistory_rs.order_by('created_date')
        rootserverhistory_rs = rootserverhistory_rs.values_list('created_date__date', 'register_anchor_location', 'rtt_max', 'rtt_avg', 'rtt_min')
        
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        # force download
        # response['Content-Disposition'] = 'attachment; filename={}.csv'.format(file_name)
        response['Content-Disposition'] = 'attachment; filename='+ filter_rootserver_name +'.csv'
    # Create the CSV writer using the HttpResponse as the "file"
        writer = csv.writer(response)
        writer.writerow(header)
        # print('&&&&&&&&&&& Print Value &&&&&&&&&&&&&', value)
        for arr in rootserverhistory_rs:
            # print('&&&&&&&&&&& Print Array &&&&&&&&&&&&&', arr)
            writer.writerow(arr)
        # for (name, sub) in zip(NAME, SUBJECT):
        #     writer.writerow([name, sub])
        print('DataFrame is written to Excel File successfully.')
        return response
        
        

        # response_data['status'] = 0
        # response_data['message'] = 'No record found in our database.'
        # response_data['data'] = []
        # return JsonResponse(response_data, status=200)

    # def post(self,request):
    #     # import requests
    #     import pandas as pd
    #     import io
    #     response_data = {}
    #     requestData = request.data
    #     today = datetime.datetime.now()
    #     d = datetime.datetime.utcnow()
    #     print(requestData)
    #     print(today)
    #     d.hour
    #     if d.hour <= 12:
    #         time_threshold = timezone.now() - timedelta(hours=12)
    #         print("Run your code here")
    #         # nothing happens, it's after 9:00 here.


        
    #     rootserverhistory_rs = RootServerLatencyCheckHistoryDetails.objects.filter(is_blocked=False, is_deleted=False, register_anchor_state__isnull=False, query_type='ping', created_date__date__gte=requestData['form_date'], created_date__date__lte=requestData['to_date'])
    #     rootserverhistory_rs = rootserverhistory_rs.filter(root_server_id__display_name=requestData['rootserver_name'])
    #     # if len(requestData['anchor_states']) > 0:
    #     #     rootserverhistory_rs = rootserverhistory_rs.filter(register_anchor_state__in=requestData['anchor_states'])
    #     rootserverhistory_rs = rootserverhistory_rs.order_by('created_date')
    #     rootserverhistory_rs = rootserverhistory_rs.values('created_date__date', 'register_anchor_location', 'rtt_avg', 'rtt_min', 'rtt_max')
    #     # rootserverhistory_rs = rootserverhistory_rs.annotate(avg_latency=Avg('rtt_max'))
    #     # rootserverhistory_rs = [{'name': x['register_anchor_state'], 'value': x['avg_latency']} for x in rootserverhistory_rs]
    #     if rootserverhistory_rs:
    #         response_data['status'] = 1
    #         response_data['message'] = 'Latency record found.'
    #         response_data['root_servers'] = list(rootserverhistory_rs)
    #         return JsonResponse(response_data, status=200)
    #     else:
    #         response_data['status'] = 0
    #         response_data['message'] = 'No record found in our database.'
    #         response_data['data'] = []
    #         return JsonResponse(response_data, status=200)

class MeasurementListResource(APIView):

    """
    GET  -> List measurements (with filters)
    POST -> Create new measurement (from Celery)
    """

    def get(self, request):

        qs = Measurement.objects.all().select_related(
            "anchor_ip_id",
            "cluster_ip_id"
        )

        # ----------------
        # Filters
        # ----------------

        status_param = request.GET.get("status")
        anchor_id = request.GET.get("anchor_id")
        command_id = request.GET.get("command_id")

        if status_param:
            qs = qs.filter(status=status_param)

        if anchor_id:
            qs = qs.filter(anchor_ip_id__anchor_id=anchor_id)

        if command_id:
            qs = qs.filter(command_id=command_id)

        qs = qs.order_by("-timestamp")

        serializer = MeasurementSerializer(qs, many=True)

        return Response({
            "count": qs.count(),
            "results": serializer.data
        })


    def post(self, request):

        serializer = MeasurementSerializer(data=request.data)

        if serializer.is_valid():
            obj = serializer.save()

            print("[MEASUREMENT CREATED]", obj.id)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class MeasurementResource(APIView):

    """
    GET -> Get single measurement by ID
    PUT -> Update measurement (RTT, status, error)
    """

    def get(self, request, id):

        try:
            obj = Measurement.objects.select_related(
                "anchor_ip_id",
                "cluster_ip_id"
            ).get(id=id)

        except Measurement.DoesNotExist:

            return Response(
                {"error": "Measurement not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MeasurementSerializer(obj)

        return Response(serializer.data)


    def put(self, request, id):

        try:
            obj = Measurement.objects.get(id=id)

        except Measurement.DoesNotExist:

            return Response(
                {"error": "Measurement not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MeasurementSerializer(
            obj,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            print("[MEASUREMENT UPDATED]", obj.id)

            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
class MeasurementByClusterIPResource(APIView):

    """
    GET -> Measurements by cluster_ip with optional date filter
    """
    def get(self, request, cluster_ip):

        qs = Measurement.objects.select_related(
            "anchor_ip_id",
            "cluster_ip_id"
        ).filter(
            cluster_ip_id__id=cluster_ip
        )

        # --------------------------
        # Date Filters (Optional)
        # --------------------------

        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        # -------------------------
        # Date Range Filter
        # -------------------------

        if start_date:

            start = parse_date(start_date)

            if not start:
                return Response(
                    {"error": "Invalid start_date format (YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            start_datetime = make_aware(
                dt.combine(start, time.min)
            )

            qs = qs.filter(timestamp__gte=start_datetime)

        if end_date:

            end = parse_date(end_date)

            if not end:
                return Response(
                    {"error": "Invalid end_date format (YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            end_datetime = make_aware(
                dt.combine(end, time.max)
            )

            qs = qs.filter(timestamp__lte=end_datetime)

        if not qs.exists():
            return Response({
                "count": 0,
                "results": []
            })

        serializer = MeasurementByIPSerializer(qs, many=True)

        return Response({
            "count": qs.count(),
            "results": serializer.data
        })

class MeasurementByIPIDDetailsResource(APIView):

    """
    GET -> Measurements by anchor_ip_id & cluster_ip_id with optional date filter
    """
    def get(self, request, cluster_id, anchor_ip_id):

        qs = Measurement.objects.select_related(
            "anchor_ip_id",
            "cluster_ip_id"
        ).filter(
            cluster_ip_id__id=cluster_id,
            anchor_ip_id__id=anchor_ip_id
        )

        # --------------------------
        # Date Filters (Optional)
        # --------------------------

        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        # -------------------------
        # Date Range Filter
        # -------------------------

        if start_date:

            start = parse_date(start_date)

            if not start:
                return Response(
                    {"error": "Invalid start_date format (YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            start_datetime = make_aware(
                dt.combine(start, time.min)
            )

            qs = qs.filter(timestamp__gte=start_datetime)

        if end_date:

            end = parse_date(end_date)

            if not end:
                return Response(
                    {"error": "Invalid end_date format (YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            end_datetime = make_aware(
                dt.combine(end, time.max)
            )

            qs = qs.filter(timestamp__lte=end_datetime)

        if not qs.exists():
            return Response({
                "count": 0,
                "results": []
            })

        serializer = MeasurementByIPSerializer(qs, many=True)

        return Response({
            "count": qs.count(),
            "results": serializer.data
        })
# def ipinfo_lookup(ip):
#     url = f"https://ipinfo.io/{ip}/json"
#     resp = requests.get(
#         url,
#         params={"token": CONFIG.IPINFO_TOKEN_NEW},
#         timeout=3,
#     )
#     print("====", resp)
#
#     if resp.status_code != 200:
#         return None
#
#     return resp
def ipinfo_lookup(ip):
    cache_key = f"ipinfo:{ip}"

    # Check cache first
    cached_data = get_cache("ip_cache", cache_key)
    if cached_data:
        print("CACHE HIT:", ip)
        return {
            "status_code": 200,
            "data": cached_data
        }

    # Call API if not cached
    url = f"https://ipinfo.io/{ip}/json"
    resp = requests.get(
        url,
        params={"token": CONFIG.IPINFO_TOKEN_NEW},
        timeout=3,
    )

    print("API CALL:", resp.status_code, ip)

    # 3. Return actual API status
    if resp.status_code != 200:
        return {
            "status_code": resp.status_code,
            "data": None
        }

    data = resp.json()

    # 4. Store in cache for 24 hours (86400 seconds)
    set_cache("ip_cache", cache_key, data, timeout=86400)

    return {
        "status_code": resp.status_code,
        "data": data
    }

def map_ipinfo(data):
    lat = lng = None
    if data.get("loc"):
        try:
            lat, lng = data["loc"].split(",")
        except ValueError:
            pass
    org = data.get("org")
    return {
        "ip": data.get("ip"),
        "city": data.get("city"),
        "state": data.get("region"),  # region → state
        "country": data.get("country"),
        "postal": data.get("postal"),
        "latitude": lat,
        "longitude": lng,
        "org": org if org else f"{data.get('asn', {}).get('asn')} {data.get('asn', {}).get('name')}",
        "address": ", ".join(
            filter(
                None,
                [
                    data.get("city"),
                    data.get("region"),
                    data.get("country"),
                ],
            )
        ),
    }
def get_active_measurement_anchors_data():
    """
    Returns filtered anchor queryset used for measurements.
    Applies CONFIG.MEASUREMENT_ANCHOR_IDS if present.
    """
    anchor_ids = CONFIG.MEASUREMENT_ANCHOR_IDS

    rs = UserAnchor.objects.filter(
        is_deleted=False,
        is_blocked=False,
        location__isnull=False,
        status="active",
        location_register_status="registered",
        anchor_id__is_online=True,
    )

    if anchor_ids:
        rs = rs.filter(anchor_id__in=anchor_ids)

    rs = rs.values(
        "id",
        "anchor_id",
        "lease_id",
        "aiori_anchor_id",
        "location",
        "user_id",
        "anchor_id__server_url",
    ).order_by("-id")

    return rs
