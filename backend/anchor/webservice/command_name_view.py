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
from backend.users.serializers import *
from backend.users.models import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import django.db.models
from django.db.models import F
from backend.anchor.models import CommendMaster
from backend.anchor.serializers import CommandViewSerializer, BlockCommandSerializer, RunCommandSerializer
import json
from django.utils import timezone


class Command_Name_View(APIView):
    def get(self, request):
        response_data = {}
        command = CommendMaster.objects.filter(is_blocked=0).values('id', 'commend_name', 'commend_description',
                                                                    'action')
        if command:
            response_data['status'] = 1
            response_data['message'] = 'Command found.'
            response_data['data'] = list(command)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No record found in our database.'
            response_data['data'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request, *args, **kwargs):
        serializer = CommandViewSerializer(data=request.data)
        if serializer.is_valid():
            requestData = serializer.validated_data
            commend_name = requestData['commend_name']
            command = CommendMaster.objects.filter(commend_name=commend_name).first()
            if not command:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response("Command Name already Found", status=status.HTTP_400_BAD_REQUEST)
        return Response("serializer not validated", status=status.HTTP_400_BAD_REQUEST)


class Block_Command_View(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BlockCommandSerializer(data=request.data)
        if serializer.is_valid():
            requestData = serializer.validated_data
            user_id = requestData['created_by']
            block_command = requestData['commend_name']
            is_super_admin = Users.objects.filter(username=user_id).values('is_superuser').first()
            if is_super_admin['is_superuser'] == True:
                block = CommendMaster.objects.filter(commend_name=block_command).update(is_blocked=1)
                return Response("Command Blocked", status=200)
            else:
                return Response("You are not SuperUser", status=200)
        else:
            return Response("User not found", status=status.HTTP_400_BAD_REQUEST)


class Run_Command_View(APIView):
    def post(self, request, *args, **kwargs):
        command_id = request.data["id"]
        get_command = CommendMaster.objects.filter(id=command_id).values_list('commend_name').first()[0]
        # if get_command=='ping':
        #    return "Execute the ping command"
        # elif get_command=='log':
        #    return "Execute the log command"
        # else:
        #    return "Invalid Command"
        return Response(get_command, status=200)
