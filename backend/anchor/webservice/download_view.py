from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import json
from django.http import JsonResponse
from django.http import HttpResponse
from datetime import datetime, timedelta, date
import django.db.models
from django.contrib.auth import get_user_model
from backend.anchor.models import *
from backend.anchor.serializers import *
import requests
from django.utils.encoding import smart_str
from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
import csv
# from django.db.models.query import QuerySet, ValuesQuerySet
from django.http import FileResponse
from rest_framework import viewsets, renderers
from rest_framework.decorators import action


def get_data(history_id):
    rs = CommendExecutionHistory.objects.filter(id=history_id).first()
    if rs:
        detailsObj = CommendExecutionHistoryDetails.objects.filter(commend_execution_history_id=rs.id).values('id',
                                                                                                              'commend_query_id',
                                                                                                              'anchor_name',
                                                                                                              'user_anchor_id__latitude',
                                                                                                              'user_anchor_id__longitude',
                                                                                                              'user_anchor_id__location')
        # print(detailsObj.query)
        if detailsObj:
            dataSet = []
            valueSet = []
            for his in detailsObj:
                # print(his['user_anchor_id__location'])
                query_id = str(his['commend_query_id'])
                # query = str(settings.INFLUXDB_HOST) + ":" + str(settings.INFLUXDB_PORT) + "/query?pretty=true&db=" + str(settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id +"'"
                query = str(settings.INFLUXDB_HOST) + "/query?pretty=true&db=" + str(
                    settings.INFLUXDB_DATABASE) + "&q=SELECT destination, rtt_avg FROM ping WHERE id='" + query_id + "'"
                # print('&&&&&&&&&&&&& query &&&&&&&&&&', query)
                result = requests.get(query)
                if result.status_code == 200:
                    json_result = result.json()
                    msg = 'Data set is ready.'
                    for val in json_result['results']:
                        # print(val)
                        if "series" in val:
                            for ser in val['series']:
                                if "values" in ser:
                                    header_list = [x.capitalize() for x in ser['columns']]
                                    header_list.extend(['Anchor', 'Latitude', 'Longitude', 'Location'])
                                    # print('************* header_list ********', header_list)
                                    for value in ser['values']:
                                        value.append(his['anchor_name'])
                                        value.append(his['user_anchor_id__latitude'])
                                        value.append(his['user_anchor_id__longitude'])
                                        value.append(his['user_anchor_id__location'])
                                        # print('************* value ********', value)
                                        valueSet.append(value)

                                    # dataSet.append({'header':header_list, 'valueset': ser['values']})
                                    # valueSet.append(ser['values'])
                                    # for value in ser['values']:
                                    #     valueSet.append(ser['values'])
                                    #     res = {ser['columns'][i]: value[i] for i in range(len(ser['columns']))}
                                    #     dataSet.append(res)
                                    # dataSet.append({'valueset': valueSet})
                                else:
                                    msg = 'Values key is not present in your data set.'
                        else:
                            msg = 'Series key is not present in your data set.'

                    # response_data['status'] = 1
                    # response_data['message'] = msg
                    # response_data['data'] = dataSet
                    # return JsonResponse(response_data, status=200)
                    # print('&&&&&&&&&&&&& -- dataSet -- &&&&&&&&&&&&', dataSet)
                    # return dataSet
            dataSet.append({'header': header_list, 'valueset': valueSet})
            return dataSet
            # else:
            #     print(0)
            #     # response_data['status'] = 0
            #     # response_data['message'] = 'Infiux DB not return any data.'
            #     # response_data['data'] = []
            #     # return JsonResponse(response_data, status=200)
            #     return dataSet
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


def export_to_csv(header, value):
    # Create the HttpResponse object with the appropriate CSV header.
    # response = HttpResponse('text/csv')
    # response['Content-Disposition'] = 'attachment; filename=quiz.csv'
    response = HttpResponse(content_type='text/csv')
    # force download
    # response['Content-Disposition'] = 'attachment; filename={}.csv'.format(file_name)
    response['Content-Disposition'] = 'attachment; filename=Periodic.csv'
    # Create the CSV writer using the HttpResponse as the "file"
    writer = csv.writer(response)
    writer.writerow(header)
    # print('&&&&&&&&&&& Print Value &&&&&&&&&&&&&', value)
    for arr in value:
        # print('&&&&&&&&&&& Print Array &&&&&&&&&&&&&', arr)
        writer.writerow(arr)
    # for (name, sub) in zip(NAME, SUBJECT):
    #     writer.writerow([name, sub])

    return response


class ExportAsCSV(APIView):
    # permission_classes = (IsAuthenticated,)
    def get(self, request, pk):
        # print('&&&&&&&&&&&&&&&&&&&', pk)
        history_id = pk
        response_data = {}
        resultSet = get_data(history_id)
        if resultSet:
            data = export_to_csv(header=resultSet[0]['header'], value=resultSet[0]['valueset'])

            return data
        else:
            # print('***************', data[0]['header'])

            return data
