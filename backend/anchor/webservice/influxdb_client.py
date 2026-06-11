from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import json
from django.http import JsonResponse
from django.http import HttpResponse
from datetime import datetime, timedelta,date
import django.db.models
from django.contrib.auth import get_user_model
from backend.anchor.models import *
from backend.anchor.serializers import *
import requests


class CommandResultByHistoryIdView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        # print('requestData', requestData)
        # print('User', user_id)
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            # query_id = str(rs.commend_query_id)
            query_id = str('4a449c14-7076-4d94-a278-2d373d516a67')
            query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg, rtt_max, rtt_min FROM ping WHERE id='" + query_id +"'"
            # print('Query', query)
            result = requests.get(query)
            if result.status_code == 200:
                json_result = result.json()
                dataSet = []
                msg = 'Data set is ready.'
                for val in json_result['results']:
                    # print(val)
                    if "series" in val:
                        for ser in val['series']:
                            if "values" in ser:
                                for value in ser['values']:
                                    res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                    dataSet.append(res)
                            else:
                                msg = 'Values key is not present in your data set.'
                    else:
                        msg = 'Series key is not present in your data set.'
                    
                response_data['status'] = 1
                response_data['message'] = msg
                response_data['data'] = dataSet
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'Infiux DB not return any data.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)


class CommandResultView(APIView):
    # permission_classes = (IsAuthenticated,)
    def get(self,request):
        user = request.user
        user_id = user.id
        print('User', user_id)
        response_data = {}
        result = requests.get("http://192.168.100.121:8086/query?pretty=true&db=RtdbSrv&q=SELECT * FROM ping")
        if result.status_code == 200:
            json_result = result.json()
            dataSet = []
            for val in json_result['results']:
                for ser in val['series']:
                    for value in ser['values']:
                        res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                        dataSet.append(res)
            response_data['status'] = 1
            response_data['message'] = 'Data set is ready.'
            response_data['data'] = dataSet
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Infiux DB not return any data.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        # print('requestData', requestData)
        # print('User', user_id)
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            query_id = str(rs.commend_query_id)
            query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT * FROM ping WHERE id='" + query_id +"'"
            # print('Query', query)
            result = requests.get(query)
            if result.status_code == 200:
                json_result = result.json()
                dataSet = []
                anchor_name = ''
                anchor_name = str(rs.anchor_names)
                msg = 'Data set is ready.'
                for val in json_result['results']:
                    # print(val)
                    if "series" in val:
                        for ser in val['series']:
                            if "values" in ser:
                                for value in ser['values']:
                                    res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))}
                                    res['anchor_name'] = anchor_name
                                    dataSet.append(res)
                            else:
                                msg = 'Values key is not present in your data set.'
                    else:
                        msg = 'Series key is not present in your data set.'
                    
                response_data['status'] = 1
                response_data['message'] = msg
                response_data['data'] = dataSet
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'Infiux DB not return any data.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class RegularZoneCommandResultView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        # print('requestData', requestData)
        # print('User', user_id)
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id)
            if detailsObj:
                dataSet = []
                anchor_name = ''
                for his in detailsObj:
                    anchor_name = str(his.anchor_name)
                    query_id = str(his.commend_query_id)
                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg, rtt_max, rtt_min FROM ping WHERE id='" + query_id +"' ORDER BY time DESC LIMIT 1"
                    # print('&&&&&&&&&&&&& query &&&&&&&&&&', query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        # print('&&&&&&&& Result &&&&&&&&&&&', json_result)
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            # print(val)
                            if "series" in val:
                                for ser in val['series']:
                                    if "values" in ser:
                                        for value in ser['values']:
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))}
                                            res['anchor_name'] = anchor_name
                                            dataSet.append(res)
                                    else:
                                        msg = 'Values key is not present in your data set.'
                            else:
                                msg = 'Series key is not present in your data set.'
                response_data['status'] = 1
                response_data['message'] = msg
                response_data['data'] = dataSet
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'This id is not in our db.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200) 
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class PeriodicCommandResultView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            ietrval = requestData['duration']
            from_date = str(requestData['from_date'])
            to_date = str(requestData['to_date'])
            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id)
            # print(detailsObj.query)
            if detailsObj:
                dataSet = []
                newDataSet = {}
                for his in detailsObj:
                    # print(his.commend_query_id)
                    query_id = str(his.commend_query_id)
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT * FROM ping WHERE id='" + query_id +"'"
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "'"


                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "'"
                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "'"
                    # print('&&&&&&&&&&&&& query &&&&&&&&&&', query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        # print('&&&&&&&& Result &&&&&&&&&&&', json_result)
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            # print(val)
                            if "series" in val:
                                for ser in val['series']:
                                    if "values" in ser:
                                        for value in ser['values']:
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                            dataSet.append(res)
                                    else:
                                        msg = 'Values key is not present in your data set.'
                            else:
                                msg = 'Series key is not present in your data set.'
                            
                        # response_data['status'] = 1
                        # response_data['message'] = msg
                        # response_data['data'] = dataSet
                        # return JsonResponse(response_data, status=200)
                        print(1)
                    else:
                        print(0)
                        # response_data['status'] = 0
                        # response_data['message'] = 'Infiux DB not return any data.'
                        # response_data['data'] = []
                        # return JsonResponse(response_data, status=200)
                if(len(dataSet) > 0):
                    # newDataSet = []
                    # newDataSet = {}
                    checkArraySet = []
                    for data in dataSet:
                        if data['destination'] in checkArraySet:
                            print(data['destination'])
                        else:
                            checkArraySet.append(data['destination'])
                            # newDataSet.append({data['destination']:[]})
                            newDataSet[data['destination']] = []
                if len(newDataSet) > 0:
                    for index, (key, value) in enumerate(newDataSet.items()):
                        # print (index, key, value)
                        for data in dataSet:
                            if key == data['destination']:
                                value.append(data)
                                # print (key, ':', data)
                    response_data['status'] = 1
                    response_data['message'] = msg
                    response_data['data'] = newDataSet
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Infiux DB not return any data.'
                    response_data['data'] = []
                    return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no history details.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class PeriodicResultView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            ietrval = requestData['duration']
            from_date = str(requestData['from_date'])
            to_date = str(requestData['to_date'])
            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id)
            if detailsObj:
                dataSet = {}
                for his in detailsObj:
                    #print('HOST', ''.join(his.commend_request_payload['hosts']))
                    host = ''.join(his.commend_request_payload['hosts'])
                    dataSet[host] = []
                    resultSet = {
                        "time": to_date,
                        "destination": host,
                        "rtt_avg": 0
                    }
                    query_id = str(his.commend_query_id)
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "'"

                    # query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "'"

                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time <= now()"
                    #print('&&&&&&&&&&&&& query &&&&&&&&&&', query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        #print(json_result)
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            # print(val)
                            if "series" in val:
                                for ser in val['series']:
                                    if "values" in ser:
                                        for value in ser['values']:
                                            # print('TestDataSet', host)
                                            # print('value', value[2])
                                            # dataSet[host].append(value[2] if value[2] else 0 )
                                            # dataSet['labels'].append(value[0])
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                            dataSet[host].append(res)
                                    else:
                                        dataSet[host].append(resultSet)
                                        # dataSet['labels'].append(from_date)
                                        msg = 'Values key is not present in your data set.'
                            else:
                                dataSet[host].append(resultSet)
                                # dataSet['labels'].append(from_date)
                                msg = 'Series key is not present in your data set.'
                        print(1)
                    else:
                        print(0)
                        # response_data['status'] = 0
                        # response_data['message'] = 'Infiux DB not return any data.'
                        # response_data['data'] = []
                        # return JsonResponse(response_data, status=200)
                response_data['status'] = 1
                response_data['message'] = msg
                response_data['data'] = dataSet
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no history details.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def put(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            ietrval = requestData['duration']
            from_date = str(requestData['from_date'])
            to_date = str(requestData['to_date'])
            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id)
            if detailsObj:
                dataSet = {}
                for his in detailsObj:
                    #print('HOST', ''.join(his.commend_request_payload['hosts']))
                    host = ''.join(his.commend_request_payload['hosts'])
                    dataSet[host] = []
                    resultSet = {
                        "time": to_date,
                        "destination": host,
                        "rtt_avg": 0
                    }
                    query_id = str(his.commend_query_id)
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "'"

                    # query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "'"

                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time <= now()"
                    #print('&&&&&&&&&&&&& query &&&&&&&&&&', query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        #print(json_result)
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            # print(val)
                            if "series" in val:
                                for ser in val['series']:
                                    if "values" in ser:
                                        for value in ser['values']:
                                            # print('TestDataSet', host)
                                            # print('value', value[2])
                                            # dataSet[host].append(value[2] if value[2] else 0 )
                                            # dataSet['labels'].append(value[0])
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                            dataSet[host].append(res)
                                    else:
                                        dataSet[host].append(resultSet)
                                        # dataSet['labels'].append(from_date)
                                        msg = 'Values key is not present in your data set.'
                            else:
                                dataSet[host].append(resultSet)
                                # dataSet['labels'].append(from_date)
                                msg = 'Series key is not present in your data set.'
                        print(1)
                    else:
                        print(0)
                        # response_data['status'] = 0
                        # response_data['message'] = 'Infiux DB not return any data.'
                        # response_data['data'] = []
                        # return JsonResponse(response_data, status=200)
                response_data['status'] = 1
                response_data['message'] = msg
                response_data['data'] = dataSet
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no history details.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class ZonePeriodicResultView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            ietrval = requestData['duration']
            from_date = str(requestData['from_date'])
            to_date = str(requestData['to_date'])
            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id, query_status='running')
            if detailsObj:
                dataSet = {}
                for his in detailsObj:
                    #print('HOST', ''.join(his.commend_request_payload['hosts']))
                    #print('ANCHOR NAME', his.anchor_name)
                    host = ''.join(his.commend_request_payload['hosts'])
                    anchor = ''.join(his.anchor_name)
                    dataSet[anchor] = []
                    # dataSet[host] = []
                    resultSet = {
                        "time": to_date,
                        "destination": host,
                        "rtt_avg": 0
                    }
                    query_id = str(his.commend_query_id)
                    # query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time <= now()"
                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time <= '" + to_date + "'"
                    # print('&&&&&&&&&&&&& query &&&&&&&&&&', query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        #print(json_result)
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            # print(val)
                            if "series" in val:
                                for ser in val['series']:
                                    if "values" in ser:
                                        for value in ser['values']:
                                            # print('TestDataSet', host)
                                            # print('value', value[2])
                                            # dataSet[host].append(value[2] if value[2] else 0 )
                                            # dataSet['labels'].append(value[0])
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                            # dataSet[host].append(res)
                                            dataSet[anchor].append(res)
                                    else:
                                        # dataSet[host].append(resultSet)
                                        dataSet[anchor].append(resultSet)
                                        # dataSet['labels'].append(from_date)
                                        msg = 'Values key is not present in your data set.'
                            else:
                                # dataSet[host].append(resultSet)
                                dataSet[anchor].append(resultSet)
                                # dataSet['labels'].append(from_date)
                                msg = 'Series key is not present in your data set.'
                        print(1)
                    else:
                        print(0)
                        # response_data['status'] = 0
                        # response_data['message'] = 'Infiux DB not return any data.'
                        # response_data['data'] = []
                        # return JsonResponse(response_data, status=200)
                response_data['status'] = 1
                response_data['message'] = msg
                response_data['data'] = dataSet
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no history details.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class PeriodicGroupByResultView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            ietrval = requestData['duration']
            # from_date = str(rs.created_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            # to_date = str(rs.query_execution_end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            from_date = str(requestData['from_date'])
            to_date = str(requestData['to_date'])
            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id)
            if detailsObj:
                dataSet = []
                newDataSet = {}
                for his in detailsObj:
                    query_id = str(his.commend_query_id)
                    host = str(his.commend_request_payload['hosts'][0])
                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "' group by destination, time(" + ietrval + ")"
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "' group by destination, time(" + ietrval + ")"
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT * FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "'"
                    #print(query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            if "series" in val:
                                for ser in val['series']:
                                    ser['columns'].append('destination')
                                    if "values" in ser:
                                        for value in ser['values']:
                                            value.append(host)
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                            dataSet.append(res)
                                    else:
                                        msg = 'Values key is not present in your data set.'
                            else:
                                msg = 'Series key is not present in your data set.'
                            
                        # response_data['status'] = 1
                        # response_data['message'] = msg
                        # response_data['data'] = dataSet
                        # return JsonResponse(response_data, status=200)
                        print(1)
                    else:
                        print(0)
                        # response_data['status'] = 0
                        # response_data['message'] = 'Infiux DB not return any data.'
                        # response_data['data'] = []
                        # return JsonResponse(response_data, status=200)
                if(len(dataSet) > 0):
                    # newDataSet = []
                    # newDataSet = {}
                    checkArraySet = []
                    for data in dataSet:
                        if data['destination'] in checkArraySet:
                            print(data['destination'])
                        else:
                            checkArraySet.append(data['destination'])
                            newDataSet[data['destination']] = []
                if len(newDataSet) > 0:
                    for index, (key, value) in enumerate(newDataSet.items()):
                        # print (index, key, value)
                        for data in dataSet:
                            if key == data['destination']:
                                value.append(data)
                                # print (key, ':', data)
                    response_data['status'] = 1
                    response_data['message'] = msg
                    response_data['data'] = newDataSet
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Infiux DB not return any data.'
                    response_data['data'] = []
                    return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no history details.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)



    def put(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            ietrval = requestData['duration']
            # from_date = str(rs.created_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            # to_date = str(rs.query_execution_end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            from_date = str(requestData['from_date'])
            to_date = str(requestData['to_date'])

            # response_data['status'] = 1
            # response_data['from_date'] = from_date
            # response_data['to_date'] = to_date
            # response_data['from_date1'] = str(datetime.strptime(requestData['from_date'], '%Y-%m-%dT%H:%M:%S.%fZ'))
            # response_data['to_date1'] = str(requestData['to_date'])
            # return JsonResponse(response_data, status=200)

            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id)
            if detailsObj:
                dataSet = []
                newDataSet = {}
                for his in detailsObj:
                    query_id = str(his.commend_query_id)
                    host = str(his.commend_request_payload['hosts'][0])
                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time <= '" + to_date + "'"
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time <= '" + to_date + "'"
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT * FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time <= '" + to_date + "'"
                    #print(query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            if "series" in val:
                                for ser in val['series']:
                                    ser['columns'].append('destination')
                                    if "values" in ser:
                                        for value in ser['values']:
                                            value.append(host)
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                            dataSet.append(res)
                                    else:
                                        msg = 'Values key is not present in your data set.'
                            else:
                                msg = 'Series key is not present in your data set.'
                            
                        # response_data['status'] = 1
                        # response_data['message'] = msg
                        # response_data['data'] = dataSet
                        # return JsonResponse(response_data, status=200)
                        print(1)
                    else:
                        print(0)
                        # response_data['status'] = 0
                        # response_data['message'] = 'Infiux DB not return any data.'
                        # response_data['data'] = []
                        # return JsonResponse(response_data, status=200)
                if(len(dataSet) > 0):
                    # newDataSet = []
                    checkArraySet = []
                    for data in dataSet:
                        if data['destination'] in checkArraySet:
                            print(data['destination'])
                        else:
                            checkArraySet.append(data['destination'])
                            newDataSet[data['destination']] = []
                if len(newDataSet) > 0:
                    for index, (key, value) in enumerate(newDataSet.items()):
                        # print (index, key, value)
                        for data in dataSet:
                            if key == data['destination']:
                                value.append(data)
                                # print (key, ':', data)
                    response_data['status'] = 1
                    response_data['message'] = msg
                    response_data['data'] = newDataSet
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Infiux DB not return any data.'
                    response_data['data'] = []
                    return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no history details.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class PeriodicZoneGroupByResultView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            ietrval = requestData['duration']
            # from_date = str(rs.created_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            # to_date = str(rs.query_execution_end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            from_date = str(requestData['from_date'])
            to_date = str(requestData['to_date'])
            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id)
            if detailsObj:
                dataSet = []
                newDataSet = {}
                for his in detailsObj:
                    query_id = str(his.commend_query_id)
                    host = str(his.commend_request_payload['hosts'][0])
                    anchor = str(his.anchor_name)
                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "' group by destination, time(" + ietrval + ")"
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "' group by destination, time(" + ietrval + ")"
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT * FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time < '" + to_date + "'"
                    #print(query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            if "series" in val:
                                for ser in val['series']:
                                    ser['columns'].append('destination')
                                    if "values" in ser:
                                        for value in ser['values']:
                                            value.append(anchor)
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                            dataSet.append(res)
                                    else:
                                        msg = 'Values key is not present in your data set.'
                            else:
                                msg = 'Series key is not present in your data set.'
                            
                        # response_data['status'] = 1
                        # response_data['message'] = msg
                        # response_data['data'] = dataSet
                        # return JsonResponse(response_data, status=200)
                        print(1)
                    else:
                        print(0)
                        # response_data['status'] = 0
                        # response_data['message'] = 'Infiux DB not return any data.'
                        # response_data['data'] = []
                        # return JsonResponse(response_data, status=200)
                if(len(dataSet) > 0):
                    # newDataSet = []
                    # newDataSet = {}
                    checkArraySet = []
                    for data in dataSet:
                        if data['destination'] in checkArraySet:
                            print(data['destination'])
                        else:
                            checkArraySet.append(data['destination'])
                            newDataSet[data['destination']] = []
                if len(newDataSet) > 0:
                    for index, (key, value) in enumerate(newDataSet.items()):
                        # print (index, key, value)
                        for data in dataSet:
                            if key == data['destination']:
                                value.append(data)
                                # print (key, ':', data)
                    response_data['status'] = 1
                    response_data['message'] = msg
                    response_data['data'] = newDataSet
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Infiux DB not return any data.'
                    response_data['data'] = []
                    return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no history details.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)



    def put(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            ietrval = requestData['duration']
            # from_date = str(rs.created_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            # to_date = str(rs.query_execution_end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
            from_date = str(requestData['from_date'])
            to_date = str(requestData['to_date'])

            # response_data['status'] = 1
            # response_data['from_date'] = from_date
            # response_data['to_date'] = to_date
            # response_data['from_date1'] = str(datetime.strptime(requestData['from_date'], '%Y-%m-%dT%H:%M:%S.%fZ'))
            # response_data['to_date1'] = str(requestData['to_date'])
            # return JsonResponse(response_data, status=200)

            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id)
            if detailsObj:
                dataSet = []
                newDataSet = {}
                for his in detailsObj:
                    query_id = str(his.commend_query_id)
                    host = str(his.commend_request_payload['hosts'][0])
                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time <= '" + to_date + "'"
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT Mean(rtt_avg) FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time <= '" + to_date + "'"
                    # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT * FROM ping WHERE id='" + query_id +"' AND time >= '" + from_date +"' AND time <= '" + to_date + "'"
                    #print(query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            if "series" in val:
                                for ser in val['series']:
                                    ser['columns'].append('destination')
                                    if "values" in ser:
                                        for value in ser['values']:
                                            value.append(host)
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                            dataSet.append(res)
                                    else:
                                        msg = 'Values key is not present in your data set.'
                            else:
                                msg = 'Series key is not present in your data set.'
                            
                        # response_data['status'] = 1
                        # response_data['message'] = msg
                        # response_data['data'] = dataSet
                        # return JsonResponse(response_data, status=200)
                        print(1)
                    else:
                        print(0)
                        # response_data['status'] = 0
                        # response_data['message'] = 'Infiux DB not return any data.'
                        # response_data['data'] = []
                        # return JsonResponse(response_data, status=200)
                if(len(dataSet) > 0):
                    # newDataSet = []
                    checkArraySet = []
                    for data in dataSet:
                        if data['destination'] in checkArraySet:
                            print(data['destination'])
                        else:
                            checkArraySet.append(data['destination'])
                            newDataSet[data['destination']] = []
                if len(newDataSet) > 0:
                    for index, (key, value) in enumerate(newDataSet.items()):
                        # print (index, key, value)
                        for data in dataSet:
                            if key == data['destination']:
                                value.append(data)
                                # print (key, ':', data)
                    response_data['status'] = 1
                    response_data['message'] = msg
                    response_data['data'] = newDataSet
                    return JsonResponse(response_data, status=200)
                else:
                    response_data['status'] = 0
                    response_data['message'] = 'Infiux DB not return any data.'
                    response_data['data'] = []
                    return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no history details.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

class PeriodicResultByIdView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        requestData = request.data
        response_data = {}
        rs = CommendExecutionHistory.objects.filter(id=requestData['id']).first()
        if rs:
            ietrval = "10s"
            detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id)
            if detailsObj:
                dataSet = {}
                for his in detailsObj:
                    print('HOST', ''.join(his.commend_request_payload['hosts']))
                    host = ''.join(his.commend_request_payload['hosts'])
                    anchor = str(his.anchor_name)
                    dataSet[anchor] = []
                    resultSet = {
                        "destination": host,
                        "rtt_avg": 0
                    }
                    query_id = str(his.commend_query_id)
                    query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT time, rtt_avg FROM ping WHERE id='" + query_id +"'"
                    # print('&&&&&&&&&&&&& query &&&&&&&&&&', query)
                    result = requests.get(query)
                    if result.status_code == 200:
                        json_result = result.json()
                        #print(json_result)
                        msg = 'Data set is ready.'
                        for val in json_result['results']:
                            # print(val)
                            if "series" in val:
                                for ser in val['series']:
                                    if "values" in ser:
                                        for value in ser['values']:
                                            arr = []
                                            # print('TestDataSet', host)
                                            # arr.append(value[0], value[1])
                                            # dataSet[host].append(value[2] if value[2] else 0 )
                                            # dataSet['labels'].append(value[0])
                                            res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))} 
                                            dataSet[anchor].append(res)
                                    else:
                                        dataSet[anchor].append(resultSet)
                                        # dataSet['labels'].append(from_date)
                                        msg = 'Values key is not present in your data set.'
                            else:
                                dataSet[anchor].append(resultSet)
                                # dataSet['labels'].append(from_date)
                                msg = 'Series key is not present in your data set.'
                        print(1)
                    else:
                        print(0)
                response_data['status'] = 1
                response_data['message'] = msg
                response_data['data'] = dataSet
                return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no history details.'
                response_data['data'] = []
                return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This id is not in our db.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)