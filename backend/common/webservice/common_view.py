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
# from django.core.mail import send_mail
import random
from django.utils import timezone
import os


class JSONResponse(HttpResponse):
    """ An HttpResponse that renders its content into JSON. """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        # kwargs['access_control_allow_origin'] = '*'
        super(JSONResponse, self).__init__(content, **kwargs)


class CountryView(generics.ListAPIView):

    def post(self, request):
        serializer = CountryViewSerializer(data=request.data)
        res = "ji"
        return res


class CountryListView(generics.ListAPIView):
    def get(self, request):
        response_data = {}
        qs = Countries.objects.filter(is_deleted=False, is_blocked=False)
        if qs.count() > 0:
            qs_data = CountryListSerializer(qs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Data found successfully'
            response_data['countries'] = qs_data.data
        else:
            response_data['status'] = 0
            response_data['message'] = 'Data not found'
            response_data['countries'] = []
        return Response(response_data, status=200)


class StateListView(generics.ListAPIView):
    def get(self, request):
        query = self.request.GET.get("country_id")
        response_data = {}
        qs = States.objects.filter(is_deleted=False, is_blocked=False)
        if query is not None:  ### Check query string is not empty
            qs = qs.filter(country_id=query)
        if qs.count() > 0:
            qs_data = StateListSerializer(qs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Data found successfully'
            response_data['states'] = qs_data.data
        else:
            response_data['status'] = 0
            response_data['message'] = 'Data not found'
            response_data['states'] = []
        return Response(response_data, status=200)


class CityListView(generics.ListAPIView):
    def get(self, request):
        query = self.request.GET.get("state_id")
        response_data = {}
        qs = Cities.objects.filter(is_deleted=False, is_blocked=False)
        if query is not None:  ### Check query string is not empty
            qs = qs.filter(state_id=query)
        if qs.count() > 0:
            qs_data = CityListSerializer(qs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Data found successfully'
            response_data['cities'] = qs_data.data
        else:
            response_data['status'] = 0
            response_data['message'] = 'Data not found'
            response_data['cities'] = []
        return Response(response_data, status=200)


class HighlightedFeaturesView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        print(user_id)
        response_data = {
            'status': 1,
            'remaining_points': 0,
            'unread_reports': 0,
            'rented_anchor': 0,
            'command_count': 0
        }
        CommendExecutionHistoryQs = CommendExecutionHistory.objects.filter(is_deleted=False, has_been_seen=False,
                                                                           user_id=user_id)
        if CommendExecutionHistoryQs.count() > 0:
            response_data['unread_reports'] = CommendExecutionHistoryQs.count()

        CommandsQs = CommendMaster.objects.filter(is_deleted=False, is_blocked=False)
        if CommandsQs.count() > 0:
            response_data['command_count'] = CommandsQs.count()

        UserSubscriptionQs = UserSubscription.objects.filter(user_id=user_id, is_deleted=False).last()
        if UserSubscriptionQs:
            response_data['remaining_points'] = UserSubscriptionQs.remaining_points

        UserAnchorQs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False,
                                                 location_register_status='registered', status='active',
                                                 user_id=user_id)
        if UserAnchorQs.count() > 0:
            response_data['rented_anchor'] = UserAnchorQs.count()
        return Response(response_data, status=200)


class UserGroupListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        response_data = {}
        qs = UserGroupMasters.objects.filter(is_deleted=False).order_by("-id")
        if qs.count() > 0:
            qs_data = UserGroupMastersSerializer(qs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Data found successfully'
            response_data['groups'] = qs_data.data
        else:
            response_data['status'] = 0
            response_data['message'] = 'Data not found'
            response_data['groups'] = []
        return Response(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        data = {}
        requestdata = request.data

        qscount = UserGroupMasters.objects.filter(is_deleted=False,
                                                  group_name__iexact=requestdata['group_name']).count()
        if qscount <= 0:
            insert_id = UserGroupMasters.objects.create(
                group_name=requestdata['group_name'],
                created_by_id=user_id,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            data = {
                'status': 1,
                'api_status': 1,
                'message': 'Group create successfully.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'message': 'Group Name already exist.',
            }
            return Response(data)

    def put(self, request):
        user = request.user
        user_id = user.id
        data = {}
        requestdata = request.data
        is_blocked = request.data.get('isblocked', None)
        is_deleted = request.data.get('is_deleted', None)

        qscount = UserGroupMasters.objects.filter(is_deleted=False, pk=requestdata['group_id']).count()
        if qscount > 0:
            obj = UserGroupMasters.objects.filter(pk=requestdata['group_id'])
            if is_blocked is not None:
                obj_id = obj.update(
                    status=is_blocked,
                    updated_at=timezone.now()
                )
            elif is_deleted is not None:
                obj_id = obj.update(
                    is_deleted=is_deleted,
                    updated_at=timezone.now()
                )
            else:
                obj_id = obj.update(
                    group_name=requestdata['group_name'],
                    updated_at=timezone.now()
                )
            data = {
                'status': 1,
                'api_status': 1,
                'message': 'Group update successfully.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'message': 'Group Name not exist.',
            }
            return Response(data)


def recursive(note, child_list):
    note_children = MenuMasters.objects.filter(parent_id=note.id)
    child_list.append(note.id)
    if note_children.count() == 0:
        return child_list
    for n in note_children:
        recursive(n, child_list)

    return child_list


def recursiveParent(note, menu_list):
    note_children = MenuMasters.objects.filter(id=note.parent_id)
    # print('************ note_children **************', note_children)
    # menu_list.append(note.id)
    if note_children.count() == 0:
        return menu_list
    for n in note_children:
        menu_list.append({'id': n.id, 'menu_name': n.menu_name, 'parent_id': n.parent_id})
        recursiveParent(n, menu_list)
    menu_list = menu_list[::-1]
    return menu_list


def create_parent_chield_node(data_set):
    a = data_set
    # a = [(1, 1), (2, 1), (3, 1), (4, 3), (5, 3), (6, 3), (7, 7), (8, 7), (9, 7)]
    # pass 1: create nodes dictionary
    nodes = {}
    for i in a:
        # print(i)
        # id, parent_id = i
        id, parent_id, menu_name, alt_name, menu_link, menu_type, module, list_orders, all_action, add_action, edit_action, delete_action, view_action, block_action, import_action, export_action, icon_class = i
        nodes[id] = {
            'id': id,
            'parent_id': parent_id,
            'menu_name': menu_name,
            'alt_name': alt_name,
            'menu_link': menu_link,
            'menu_type': menu_type,
            'module': module,
            'list_orders': list_orders,
            'all_action': all_action,
            'add_action': add_action,
            'edit_action': edit_action,
            'delete_action': delete_action,
            'view_action': view_action,
            'block_action': block_action,
            'import_action': import_action,
            'export_action': export_action,
            'icon_class': icon_class
        }
        # nodes[id] = {'id': id, 'parent_id': parent_id, 'menu_name': menu_name}

    # pass 2: create trees and parent-child relations
    forest = []
    for i in a:
        id, parent_id, menu_name, alt_name, menu_link, menu_type, module, list_orders, all_action, add_action, edit_action, delete_action, view_action, block_action, import_action, export_action, icon_class = i
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


class MenuMasterListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query = 'frontend'
        if self.request.GET.get("type"):
            query = self.request.GET.get("type")
        response_data = {}
        qs = MenuMasters.objects.filter(is_deleted=False, menu_type=query).values_list('id', 'parent_id', 'menu_name',
                                                                                       'alt_name', 'menu_link',
                                                                                       'menu_type', 'module',
                                                                                       'list_orders', 'all_action',
                                                                                       'add_action', 'edit_action',
                                                                                       'delete_action', 'view_action',
                                                                                       'block_action', 'import_action',
                                                                                       'export_action',
                                                                                       'icon_class').order_by('id')
        # print(qs.query)
        if qs.count() > 0:
            # qs_data = MenuMastersSerializer(qs, many=True)
            set_data = create_parent_chield_node(qs)
            response_data['status'] = 1
            response_data['message'] = 'Data found successfully'
            response_data['menu'] = set_data
        else:
            response_data['status'] = 0
            response_data['message'] = 'Data not found'
            response_data['menu'] = []
        return Response(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        data = {}
        requestdata = request.data
        print(requestdata)
        qscount = MenuMasters.objects.filter(is_deleted=False, menu_name__iexact=requestdata['menu_name'],
                                             menu_type=requestdata['menu_type']).count()
        if qscount <= 0:
            obj = MenuMasters.objects.create(
                menu_name=requestdata['menu_name'],
                alt_name=requestdata['menu_name'],
                menu_link=requestdata['menu_link'],
                menu_type=requestdata['menu_type'],
                module=requestdata['module'],
                parent_id=requestdata['parent'],
                list_orders=requestdata['list_orders'],
                all_action=requestdata['all_action'],
                icon_class=requestdata['icon_class'],
                created_by_id=user_id,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            data = {
                'status': 1,
                'api_status': 1,
                'message': 'Menu create successfully.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'message': 'Menu Name already exist.',
            }
            return Response(data)

    def put(self, request):
        user = request.user
        user_id = user.id
        data = {}
        response_data = {}
        requestdata = request.data
        is_blocked = request.data.get('isblocked', None)
        is_deleted = request.data.get('is_deleted', None)

        qscount = MenuMasters.objects.filter(is_deleted=False, pk=request.data['menu_id']).count()
        if qscount > 0:
            if is_blocked is not None:
                parent_obj = MenuMasters.objects.filter(pk=request.data['menu_id']).first()
                result_arr = recursive(parent_obj, [])
                if len(result_arr) > 0:
                    for item in result_arr:
                        obj_id = MenuMasters.objects.filter(pk=item).update(
                            status=is_blocked,
                            updated_at=timezone.now()
                        )
            elif is_deleted is not None:
                parent_obj = MenuMasters.objects.filter(pk=request.data['menu_id']).first()
                result_arr = recursive(parent_obj, [])
                for item in result_arr:
                    obj_id = MenuMasters.objects.filter(pk=item).update(
                        is_deleted=is_deleted,
                        updated_at=timezone.now()
                    )
            else:
                obj_id = MenuMasters.objects.filter(pk=request.data['menu_id']).update(
                    menu_name=requestdata['menu_name'],
                    alt_name=requestdata['menu_name'],
                    menu_link=requestdata['menu_link'],
                    module=requestdata['module'],
                    parent_id=requestdata['parent'],
                    list_orders=requestdata['list_orders'],
                    all_action=requestdata['all_action'],
                    icon_class=requestdata['icon_class'],
                    updated_at=timezone.now()
                )
            data = {
                'status': 1,
                'api_status': 1,
                'message': 'Menu update successfully.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'message': 'Group Name not exist.',
            }
            return Response(data)


class UserGroupManagmentView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data = {}
        query = 0
        if self.request.GET.get("role_id"):
            query = self.request.GET.get("role_id")
        response_data = {}
        qs = UserGroup.objects.filter(is_deleted=False, status=1)
        # print(qs.query)
        if query != 0:
            qs = qs.filter(group_id=query)
        if qs.count() > 0:
            qs_data = UserGroupSerializer(qs, many=True)
            data = {
                'status': 1,
                'api_status': 1,
                'group_details': qs_data.data,
                'message': 'Data found successfully.'
            }
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'group_details': [],
                'message': 'Data not found.'
            }
        return Response(data)

    def post(self, request):
        user = request.user
        user_id = user.id
        data = {}
        requestdata = request.data
        print(requestdata)
        if len(requestdata['user_ids']) > 0:
            ## First Delete Previous Record
            Obj = UserGroup.objects.filter(is_deleted=False, group_id=requestdata['group_id']).delete()
            #### Insert New Object
            for m in requestdata['user_ids']:
                obj = UserGroup.objects.create(
                    user_id=m,
                    group_id=requestdata['group_id'],
                    created_by_id=user_id,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
            data = {
                'status': 1,
                'api_status': 1,
                'message': 'Add user in user group successfully.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'message': 'Please select user for add this group.',
            }
            return Response(data)

    def put(self, request):
        user = request.user
        user_id = user.id
        data = {}
        response_data = {}
        requestdata = request.data
        is_blocked = request.data.get('isblocked', None)
        is_deleted = request.data.get('is_deleted', None)

        qscount = UserGroup.objects.filter(is_deleted=False, pk=request.data['user_group_id']).count()
        if qscount > 0:
            obj = UserGroup.objects.filter(pk=request.data['user_group_id'])
            if is_blocked is not None:
                obj_id = obj.update(
                    status=is_blocked,
                    updated_at=timezone.now()
                )
            elif is_deleted is not None:
                obj_id = obj.update(
                    is_deleted=is_deleted,
                    updated_at=timezone.now()
                )
            else:
                obj_id = obj.update(
                    user_id=requestdata['user_id'],
                    group_id=requestdata['group_id'],
                    updated_at=timezone.now()
                )
            data = {
                'status': 1,
                'api_status': 1,
                'message': 'User group update successfully.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'message': 'This user is not exist in this group.',
            }
            return Response(data)


class MenuByParentListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        # parent_id = parent
        query = 'frontend'
        if self.request.GET.get("type"):
            query = self.request.GET.get("type")
        response_data = {}
        qs = MenuMasters.objects.filter(is_deleted=False, menu_type=query).values_list('id', 'parent_id', 'menu_name',
                                                                                       'alt_name', 'menu_link',
                                                                                       'menu_type', 'module',
                                                                                       'list_orders', 'all_action',
                                                                                       'add_action', 'edit_action',
                                                                                       'delete_action', 'view_action',
                                                                                       'block_action', 'import_action',
                                                                                       'export_action').order_by(
            'list_orders')
        # print(qs.query)
        if qs.count() > 0:
            # qs_data = MenuMastersSerializer(qs, many=True)
            set_data = create_parent_chield_node(qs)
            response_data['status'] = 1
            response_data['message'] = 'Data found successfully'
            response_data['menu'] = set_data
        else:
            response_data['status'] = 0
            response_data['message'] = 'Data not found'
            response_data['menu'] = []
        return Response(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        data = {}
        requestdata = request.data

        qs = MenuMasters.objects.filter(is_deleted=False, menu_type=requestdata['type'],
                                        parent_id=requestdata['parent_id']).order_by('list_orders')
        if qs.count() > 0:
            qs_data = MenuMastersListSerializer(qs, many=True)
            data = {
                'status': 1,
                'api_status': 1,
                'menu_list': qs_data.data,
                'message': 'Menu list generated.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'menu_list': [],
                'message': 'Menu list not found.',
            }
            return Response(data)


class MenuByIdListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_id = user.id
        data = {}
        requestdata = request.data

        qs = MenuMasters.objects.filter(is_deleted=False, pk=requestdata['menu_id']).first()
        if qs:
            qs_data = MenuMastersSerializer(qs)
            result = recursiveParent(qs, [])
            # print('&&&&&&&&&&&&&&&&&&&&&&&&&&', result)
            serialize_data = qs_data.data
            serialize_data['parent_menu_arr'] = result
            # print(serialize_data)
            data = {
                'status': 1,
                'api_status': 1,
                'menu': serialize_data,
                'message': 'Menu details.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'menu': [],
                'message': 'Menu not found.',
            }
            return Response(data)


class MenuByUserGroupView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query = 0
        if self.request.GET.get("role_id"):
            query = self.request.GET.get("role_id")
        response_data = {}
        # qs = UserGroup.objects.filter(is_deleted=False, status=1).values_list('id', flat=True).order_by('-id')
        qs = RoleMenuPermission.objects.filter(is_deleted=False, status=1).values_list('menu_id', flat=True).order_by(
            '-id')
        if query != 0:
            qs = qs.filter(group_id=query)
        print(qs)
        if qs.count() > 0:
            # permitionObj = RoleMenuPermission.objects.filter(is_deleted=False, status=1, group_id__in=qs).values_list('menu_id', flat=True).order_by('-id')
            # print(permitionObj)
            response_data['status'] = 1
            response_data['message'] = 'Data found successfully'
            response_data['menu'] = qs
        else:
            response_data['status'] = 0
            response_data['message'] = 'Data not found'
            response_data['menu'] = []
        return Response(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        data = {}
        requestdata = request.data
        print('************ requestdata *************', requestdata)
        if len(requestdata['menu_ids']) > 0:
            #### Delete Object First
            Obj = RoleMenuPermission.objects.filter(group_id=requestdata['role_id']).delete()
            #### Insert New Object
            for m in requestdata['menu_ids']:
                obj = RoleMenuPermission.objects.create(
                    menu_id=m,
                    group_id=requestdata['role_id'],
                    created_by_id=user_id,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
            if obj:
                permitionObj = RoleMenuPermission.objects.filter(is_deleted=False, status=1,
                                                                 group_id=requestdata['role_id']).values_list('menu_id',
                                                                                                              flat=True).order_by(
                    '-id')
                print(permitionObj)
                if permitionObj.count() > 0:
                    data = {
                        'status': 1,
                        'api_status': 1,
                        'menu': permitionObj,
                        'message': 'Menu add successfully.',
                    }
                else:
                    data = {
                        'status': 0,
                        'api_status': 0,
                        'menu': [],
                        'message': 'Menu add failure.',
                    }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'menu': [],
                'message': 'Menu not found.',
            }
            return Response(data)


class UserListWethoutGroupView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        data = {}
        Obj = UserGroup.objects.filter(is_deleted=False).values_list('user_id', flat=True)
        print(Obj)
        if Obj:
            # User = get_user_model()
            UserQS = CustomUser.objects.filter(is_blocked=False, is_deleted=False).exclude(id__in=Obj).order_by("-id")
            if UserQS:
                serializer = UserSerializer(UserQS, many=True)
                data = {
                    'status': 1,
                    'api_status': 1,
                    'users': serializer.data,
                    'message': 'User found successfully.',
                }
            else:
                data = {
                    'status': 0,
                    'api_status': 0,
                    'users': [],
                    'message': 'User found successfully.',
                }

            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'message': 'User not found.',
            }
            return Response(data)

    def post(self, request):
        user = request.user
        user_id = user.id
        data = {}
        requestdata = request.data
        Obj = UserGroup.objects.filter(is_deleted=False).values_list('user_id', flat=True).exclude(
            group_id=requestdata['group_id'])
        print(Obj.query)
        if Obj:
            # User = get_user_model()
            UserQS = CustomUser.objects.filter(is_blocked=False, is_deleted=False, is_superuser=False,
                                          is_email_verified=True).exclude(id__in=Obj).order_by("-id")
            if UserQS:
                serializer = UserSerializer(UserQS, many=True)
                data = {
                    'status': 1,
                    'api_status': 1,
                    'users': serializer.data,
                    'message': 'User found successfully.',
                }
            else:
                data = {
                    'status': 0,
                    'api_status': 0,
                    'users': [],
                    'message': 'User found successfully.',
                }

            return Response(data)
        else:
            UserQS = CustomUser.objects.filter(is_blocked=False, is_deleted=False, is_superuser=False,
                                          is_email_verified=True).order_by("-id")
            if UserQS:
                serializer = UserSerializer(UserQS, many=True)
                data = {
                    'status': 1,
                    'api_status': 1,
                    'users': serializer.data,
                    'message': 'User found successfully.',
                }
            return Response(data)


class UserListByGroupView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_id = user.id
        data = {}
        requestdata = request.data
        print(requestdata)
        Obj = UserGroup.objects.filter(is_deleted=False, group_id=requestdata['group_id']).values_list('user_id',
                                                                                                       flat=True)
        print(Obj)
        if Obj:
            # User = get_user_model()
            UserQS = CustomUser.objects.filter(is_blocked=False, is_deleted=False, id__in=Obj).order_by("-id")
            if UserQS:
                serializer = UserSerializer(UserQS, many=True)
                data = {
                    'status': 1,
                    'api_status': 1,
                    'users': serializer.data,
                    'message': 'User found successfully.',
                }
            else:
                data = {
                    'status': 0,
                    'api_status': 0,
                    'users': [],
                    'message': 'User found successfully.',
                }

            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'message': 'User not found.',
            }
            return Response(data)


class UserMenuListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        #print('********************', user_id)
        data = {}
        requestdata = request.data

        qs = UserGroup.objects.filter(is_deleted=False, status=1, user_id=user_id).first()
        if qs:
            permission_qs = RoleMenuPermission.objects.filter(is_deleted=False, status=1,
                                                              group_id=qs.group_id).values_list('menu_id', flat=True)
            #print('&&&&&&&&&&&&&&&&&&&&&&&&&', permission_qs)
            if permission_qs:
                query = MenuMasters.objects.filter(is_deleted=False, id__in=permission_qs).values_list('id',
                                                                                                       'parent_id',
                                                                                                       'menu_name',
                                                                                                       'alt_name',
                                                                                                       'menu_link',
                                                                                                       'menu_type',
                                                                                                       'module',
                                                                                                       'list_orders',
                                                                                                       'all_action',
                                                                                                       'add_action',
                                                                                                       'edit_action',
                                                                                                       'delete_action',
                                                                                                       'view_action',
                                                                                                       'block_action',
                                                                                                       'import_action',
                                                                                                       'export_action',
                                                                                                       'icon_class').order_by(
                    'id')
                if query:
                    set_data = create_parent_chield_node(query)
                    data = {
                        'status': 1,
                        'api_status': 1,
                        'menu': set_data,
                        'message': 'Menu details.',
                    }
                else:
                    data = {
                        'status': 0,
                        'api_status': 0,
                        'menu': [],
                        'message': 'Menu details.',
                    }
            else:
                data = {
                    'status': 0,
                    'api_status': 0,
                    'menu': [],
                    'message': 'Menu details.',
                }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'menu': [],
                'message': 'Menu not found.',
            }
            return Response(data)


class ResearchPageLayoutView(generics.ListAPIView):
    def get(self, request):
        data = {}
        requestdata = request.data

        qs = ResearchPageLayouts.objects.filter(is_deleted=False, status=1, layout_parent=0).order_by('layout_position')
        if qs:
            serializer = ResearchPageLayoutsSerializer(qs, many=True)
            # set_data = create_parent_chield_node(query)
            for parent in serializer.data:
                parent['chield'] = []
                chiqs = ResearchPageLayouts.objects.filter(is_deleted=False, status=1,
                                                           layout_parent=parent['id']).order_by('layout_position')
                if chiqs:
                    serializer1 = ResearchPageLayoutsSerializer(chiqs, many=True)
                    parent['chield'] = serializer1.data
            data = {
                'status': 1,
                'api_status': 1,
                'layouts': serializer.data,
                'message': 'Layouts details.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'layouts': [],
                'message': 'Layouts not found.',
            }
            return Response(data)


class AnchorLocationView(generics.ListAPIView):
    def get(self, request):
        data = {}
        requestdata = request.data

        qs = UserAnchor.objects.filter(is_blocked=False, is_deleted=False, status='active',
                                       location_register_status='registered')
        qs = qs.values('id', 'latitude', 'longitude', 'address', 'anchor_id__anchor_name', 'location',
                       'anchor_id__ip_type', 'anchor_id__public_ip', 'anchor_id__ip_v6')
        qs = qs.order_by('-id')
        if qs:
            data = {
                'status': 1,
                'api_status': 1,
                'data': list(qs),
                'message': 'Anchar details.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'data': [],
                'message': 'Anchar not found.',
            }
            return Response(data)


class UnicastAnchorLocationView(generics.ListAPIView):
    def get(self, request):
        data = {}
        requestdata = request.data

        rs = UserAnchor.objects.filter(is_deleted=False, is_blocked=False, status="active",
                                       location_register_status="registered", anchor_id__is_online=True)
        rs = rs.filter(Q(anchor_id__anchor_name='nats-moh-anchor') | Q(anchor_id__anchor_name='nats-gwh-anchor') | Q(
            anchor_id__anchor_name='nats-kol-anchor') | Q(anchor_id__anchor_name='nats-mum-anchor') | Q(
            anchor_id__anchor_name='nats-blr-anchor'))
        rs = rs.values('id', 'anchor_id__anchor_name', 'latitude', 'longitude', 'address', 'location',
                       'anchor_id__ip_type', 'anchor_id__public_ip', 'anchor_id__ip_v6'
                       )
        rs = rs.order_by('-id')
        if rs:
            data = {
                'status': 1,
                'api_status': 1,
                'data': list(rs),
                'message': 'Unicast anchar details.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'data': [],
                'message': 'Unicast anchar not found.',
            }
            return Response(data)


def encode_image_base64(full_path):
    image = ''
    if full_path != "":
        with open(full_path, 'rb') as imgFile:
            image = base64.b64encode(imgFile.read())
    return image


class BlogPostView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        #print('***********', requestData)
        if len(requestData['content']) > 200:
            #print('&&&&&&&&&&&&&&&&&&&&&&&&&&&', len(requestData['content']))
            info = requestData['content'][0: 200] + '......'
            #print('&&&&&&&&&&&&& IF &&&&&&&&&&&&&&', len(info))
        else:
            #  print('&&&&&&&&&&&&&&&&&&&&&&&&&&&', 'LEN LESS')
            info = requestData['content']
            #print('&&&&&&&&&&&& ELSE &&&&&&&&&&&&&&&', len(info))
        if user:
            # info = (requestData['content'][:200] + '......') if len(requestData['content']) < 200 else requestData['content']
            obj = blogs.objects.create(
                created_by_id=user_id,
                blog_title=requestData['title'],
                smoll_content=info,
                content=requestData['content'],
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            response_data['status'] = 1
            response_data['message'] = 'Blog save successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Blog save failure.'
            return JsonResponse(response_data, status=200)


class BlogView(APIView):
    # permission_classes = (IsAuthenticated,)
    def get(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        blog_data = []
        rs = blogs.objects.filter(is_deleted=False, is_blocked=False)
        rs = rs.values('id', 'blog_title', 'smoll_content', 'created_at', 'created_by__first_name',
                       'created_by__last_name', 'created_by__profile_image')
        rs = rs.order_by('-created_at')
        if rs:
            # serializer = BlogSerializer(rs, many=True)
            # for details in rs:
            #     image = ''
            #     print('Profile Image', details['created_by__profile_image'])
            #     profile_image_name = details['created_by__profile_image']
            #     print('profile_image_name Image', profile_image_name)
            #     if profile_image_name is not None:
            #         if os.path.exists('media/profile_image/' + profile_image_name):
            #             base64_image = encode_image_base64(settings.MEDIA_ROOT + '/profile_image/' + profile_image_name)
            #             details['created_by__profile_image'] = base64_image
            #             image = base64_image
            #             # print('Profile Image', base64_image)
            #             # details['profile_image'] = null
            #     blog_data.append({
            #         'id':details['id'],
            #         'title':details['blog_title'],
            #         'content':details['smoll_content'],
            #         'user_name':details['created_by__first_name'] +' '+ details['created_by__last_name'],
            #         'user_image':image
            #         })
            response_data['status'] = 1
            response_data['message'] = 'Blog list.'
            response_data['blogs'] = list(rs)
            # response_data['blogs1'] = blog_data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Blog list blank.'
            response_data['anchor'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        rs = blogs.objects.filter(is_deleted=False, is_blocked=False, id=requestData['blog_id'])
        rs = rs.values('id', 'blog_title', 'content', 'created_at', 'created_by__first_name', 'created_by__last_name',
                       'created_by__profile_image')
        if rs:
            response_data['status'] = 1
            response_data['message'] = 'Blog details.'
            response_data['blog'] = list(rs)
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No blog in our db.'
            return JsonResponse(response_data, status=200)



class SiteSettingsView(APIView):
    # permission_classes = (IsAuthenticated,)
    def get(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        rs = DefaultSiteSetup.objects.filter(is_deleted=False)
        # rs=rs.values('id', 'rd3mn_server_url', 'rd3mn_api_key', 'rd3mn_api_key_value', 'is_blocked')
        rs = rs.order_by('-id')
        if rs:
            serializer = SiteSettingsSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Settings list.'
            response_data['settings'] = serializer.data
            # response_data['blogs1'] = blog_data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Settings list blank.'
            response_data['anchor'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        rs = DefaultSiteSetup.objects.filter(is_deleted=False, is_blocked=False)
        rs = rs.values('id')
        if rs:
            for x in rs:
                DefaultSiteSetup.objects.filter(id=x['id']).update(is_blocked=True)

            obj = DefaultSiteSetup.objects.create(
                created_by_id=user_id,
                rd3mn_server_url=requestData['url'],
                rd3mn_api_key=requestData['key'],
                rd3mn_api_key_value=requestData['value'],
                created_date=timezone.now(),
                modified_date=timezone.now(),
            )
            response_data['status'] = 1
            response_data['message'] = 'Settings save successfully.'
            return JsonResponse(response_data, status=200)
        else:
            obj = DefaultSiteSetup.objects.create(
                created_by_id=user_id,
                rd3mn_server_url=requestData['url'],
                rd3mn_api_key=requestData['key'],
                rd3mn_api_key_value=requestData['value'],
                created_date=timezone.now(),
                modified_date=timezone.now(),
            )
            response_data['status'] = 1
            response_data['message'] = 'Settings save successfully.'
            return JsonResponse(response_data, status=200)

    def put(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        is_blocked = request.data.get('is_blocked', None)
        is_deleted = request.data.get('is_deleted', None)
        qscount = DefaultSiteSetup.objects.filter(is_deleted=False, pk=request.data['settings_id']).count()
        if qscount > 0:
            obj = DefaultSiteSetup.objects.filter(pk=request.data['settings_id'])
            if is_blocked is not None:
                obj_id = obj.update(
                    is_blocked=is_blocked,
                    modified_date=timezone.now()
                )
            elif is_deleted is not None:
                obj_id = obj.update(
                    is_deleted=is_deleted,
                    modified_date=timezone.now()
                )
            response_data['status'] = 0
            response_data['message'] = 'Settings update successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This user is not admin.'
            return JsonResponse(response_data, status=200)


class SiteSettingsDetailsView(APIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        rs = DefaultSiteSetup.objects.filter(is_deleted=False, pk=requestData['settings_id'])
        if rs:
            serializer = SiteSettingsSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Settings details.'
            response_data['settings'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Settings details not found.'
            return JsonResponse(response_data, status=200)

    def put(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        is_blocked = request.data.get('is_blocked', None)
        is_deleted = request.data.get('is_deleted', None)
        qsobj = DefaultSiteSetup.objects.filter(is_deleted=False, pk=request.data['settings_id']).count()
        if qsobj > 0:
            obj = DefaultSiteSetup.objects.filter(pk=request.data['settings_id'])
            obj_id = obj.update(
                rd3mn_server_url=request.data['url'],
                rd3mn_api_key=request.data['key'],
                rd3mn_api_key_value=request.data['value'],
                modified_date=timezone.now()
            )
            response_data['status'] = 1
            response_data['message'] = 'Settings update successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This settings is not update.'
            return JsonResponse(response_data, status=200)



