import logging
from decimal import Decimal, InvalidOperation
from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from backend.subscription.serializers import *
from backend.subscription.models import *
from django.http import JsonResponse
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import socket
from django.utils import timezone
from django.db.models import F, Max, Count, Sum, Avg, Q, Subquery, OuterRef

from backend.anchor.models import CommendExecutionHistory
from backend.subscription.models import  UserSubscription
import csv

logger = logging.getLogger(__name__)
User = get_user_model()
class UserSubscriptionView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        print("data ....", request.GET)
        user_id = user.id
        requestdata = request.data
        response_data = {}
        data = []
        rs = UserSubscription.objects.filter(user_id=user_id, is_deleted=False, insert_status='earn').first()
        if rs:
            serializer = UserSubscriptionSerializer(rs).data
            qsumearn = UserSubscription.objects.filter(user_id=user_id, is_deleted=False,
                                                       insert_status='earn').aggregate(
                total_earn_points=Sum('earn_points'))
            if qsumearn:
                serializer['earned_points'] = qsumearn['total_earn_points']
                serializer['total_points'] = qsumearn['total_earn_points']
            qs = UserSubscription.objects.filter(user_id=user_id, is_deleted=False, insert_status='spend').last()
            if qs:
                qsum = UserSubscription.objects.filter(user_id=user_id, is_deleted=False,
                                                       insert_status='spend').aggregate(
                    total_used_points=Sum('used_points'))
                if qsum:
                    serializer['used_points'] = qsum['total_used_points']
                serializer['remaining_points'] = qs.remaining_points
            data.append(serializer)
            # for subscription in serializer.data:
            #     qs =UserSubscription.objects.filter(user_id=user_id, is_deleted=False, insert_status='spend').last()
            #     if qs:
            #         qsum = UserSubscription.objects.filter(user_id=user_id, is_deleted=False, insert_status='spend').aggregate(total_used_points = Sum('used_points'))
            #         if qsum:
            #             subscription['used_points'] = qsum['total_used_points']
            #         subscription['remaining_points'] = qs.remaining_points
            response_data['status'] = 1
            response_data['message'] = 'Plan found.'
            response_data['plans'] = data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No Plan found.'
            response_data['plans'] = []
            return JsonResponse(response_data, status=200)


def add_points_for_anchor_user(user_id, add_points, run_command_name, command_run_time):
    print('User Points Add', user_id)
    print('User Points Add', add_points)
    print('User Points Add', run_command_name)
    print('User Points Add', command_run_time)
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    subscriptionObj = UserSubscription.objects.filter(user_id=user_id, is_deleted=False).last()
    if subscriptionObj:
        last_balance_points = subscriptionObj.remaining_points
        total_points = subscriptionObj.total_points + add_points   # Modified On 21.08.2025
        remaining_points = (last_balance_points + add_points)
        print('User Points Add last_balance_points', last_balance_points)
        print('User Points Add remaining_points', remaining_points)
        ## Insert into table
        obj = UserSubscription.objects.create(
            user_id=user_id,
            package_id=subscriptionObj.package_id,
            # total_points=last_balance_points,       # Modified On 21.08.2025
            total_points=total_points,
            earn_points=add_points,
            remaining_points=remaining_points,
            package_activation_date=subscriptionObj.package_activation_date,
            package_deactivation_date=subscriptionObj.package_deactivation_date,
            created_date=timezone.now(),
            modified_date=timezone.now(),
            insert_status='earn',
            command_name=run_command_name,
            run_time=command_run_time,
            ipAddress=IPAddr
        )


class PointUtilizationView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        requestdata = request.data
        response_data = {}
        # rs =UserSubscription.objects.filter(user_id=user_id, is_deleted=False, insert_status='spend').order_by('-id')
        rs = UserSubscription.objects.filter(user_id=user_id, is_deleted=False).order_by('-id')[:100]
        if rs:
            serializer = UserSubscriptionSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'I was able to get the points you used.'
            response_data['utilization'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Your point was not used.'
            response_data['utilization'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request):
        """
        Point utilization status code:

        user have no subscription points earn entry = 0

        successfully deduct point = 1

        remaining_points is less then deduct point = 2
        """
        user = request.user
        user_id = user.id
        requestdata = request.data
        response_data = {}
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        ## To Do run time wise set used point
        ## Now default used point is 5
        used_points = requestdata['utilize_point']
        anchor_user_id = requestdata['anchor_user_id']
        anchor_user_ids = requestdata['anchor_user_ids']
        # print('USER ID', user_id)
        # print('ANCHOR USER ID', anchor_user_id)
        # response_data['status'] = 2
        # response_data['message'] = 'You have not enough point for command execution.'
        # return JsonResponse(response_data, status=200)
        if len(anchor_user_ids) > 0:
            for anchor_id in anchor_user_ids:
                subscriptionObj = UserSubscription.objects.filter(user_id=user_id, is_deleted=False).last()
                if subscriptionObj:
                    print(subscriptionObj.id)
                    # utilizeObj = UserSubscription.objects.filter(user_id=user_id, is_deleted=False, insert_status='spend').last()
                    # if utilizeObj: 
                    ## calculate point deduction from this object
                    last_balance_points = subscriptionObj.remaining_points
                    remaining_points = (last_balance_points - used_points)
                    ## Check enough point have or not
                    if used_points > last_balance_points:
                        print('Used point bigger')
                        response_data['status'] = 2
                        response_data['message'] = 'You have not enough point foanchor_user_idr command execution.'
                        return JsonResponse(response_data, status=200)
                    else:
                        if (user_id != anchor_id):
                            add_points_for_anchor_user(anchor_id, used_points, requestdata['command_name'],
                                                       requestdata['run_time'])
                        ## Insert into table
                        obj = UserSubscription.objects.create(
                            user_id=user_id,
                            package_id=subscriptionObj.package_id,
                            total_points=last_balance_points,
                            used_points=used_points,
                            remaining_points=remaining_points,
                            package_activation_date=subscriptionObj.package_activation_date,
                            package_deactivation_date=subscriptionObj.package_deactivation_date,
                            created_date=timezone.now(),
                            modified_date=timezone.now(),
                            insert_status='spend',
                            command_name=requestdata['command_name'],
                            run_time=requestdata['run_time'],
                            ipAddress=IPAddr
                        )
            response_data['status'] = 1
            response_data['message'] = 'Point deduct successfuly.'
            return JsonResponse(response_data, status=200)
        else:
            subscriptionObj = UserSubscription.objects.filter(user_id=user_id, is_deleted=False).last()
            if subscriptionObj:
                print(subscriptionObj.id)
                #print("I am here at student creation................")
                # utilizeObj = UserSubscription.objects.filter(user_id=user_id, is_deleted=False, insert_status='spend').last()
                # if utilizeObj: 
                ## calculate point deduction from this object
                last_balance_points = subscriptionObj.remaining_points
                remaining_points = (last_balance_points - used_points)
                ## Check enough point have or not
                if used_points > last_balance_points:
                    print('Used point bigger')
                    response_data['status'] = 2
                    response_data['message'] = 'You have not enough point foanchor_user_idr command execution.'
                    return JsonResponse(response_data, status=200)
                else:
                    if (user_id != anchor_user_id):
                        add_points_for_anchor_user(anchor_user_id, used_points, requestdata['command_name'],
                                                   requestdata['run_time'])
                    ## Insert into table
                    obj = UserSubscription.objects.create(
                        user_id=user_id,
                        package_id=subscriptionObj.package_id,
                        total_points=last_balance_points,
                        used_points=used_points,
                        remaining_points=remaining_points,
                        package_activation_date=subscriptionObj.package_activation_date,
                        package_deactivation_date=subscriptionObj.package_deactivation_date,
                        created_date=timezone.now(),
                        modified_date=timezone.now(),
                        insert_status='spend',
                        command_name=requestdata['command_name'],
                        run_time=requestdata['run_time'],
                        ipAddress=IPAddr
                    )
                    response_data['status'] = 1
                    response_data['message'] = 'Point deduct successfully.'
                    return JsonResponse(response_data, status=200)
            else:
                response_data['status'] = 0
                response_data['message'] = 'You have no earn points.'
                return JsonResponse(response_data, status=200)


# def point_add(user_id, point_add):
#     utilizeObj = UserSubscription.objects.filter(user_id=user_id, is_deleted=False).last()
#     if utilizeObj:
#         remaining_points = utilizeObj.remaining_points
#         previous_point = remaining_points
#         present_point = int(remaining_points) + int(point_add)
#         package_id = utilizeObj.package_id
#         ## Insert into table
#         obj = UserSubscription.objects.create(
#                 user_id=user_id,
#                 package_id=package_id,
#                 total_points=previous_point,
#                 earn_points=point_add,
#                 remaining_points=present_point,
#                 # package_activation_date=package_activation_date,
#                 # package_deactivation_date=package_deactivation_date,
#                 created_date=timezone.now(),
#                 modified_date=timezone.now(),
#                 insert_status='earn',
#                 command_name='Add New Point'
#         )
#         return 1
#     else:
#         return 0

def point_add(user_id=None, points=0, user_type=None): # Modified On 21.08.2025
    """
    Add points either to a single user (via user_id) or to all faculty (via user_type='faculty').
    Returns 1 if at least one subscription updated, else 0.
    """
    # validate amount
    try:
        amount = Decimal(str(points))
    except (InvalidOperation, TypeError):
        logger.error("Invalid points value: %r", points)
        return 0
    if amount <= 0:
        logger.warning("Non-positive points value: %s", amount)
        return 0

    updated_count = 0

    # bulk: all faculty
    if user_type == "faculty":
        faculty_users = User.objects.filter(
            is_faculty=True,
            is_blocked=False,
            is_deleted=False
        )
        if not faculty_users.exists():
            logger.info("No active faculty users found.")
            return 0

        with transaction.atomic():
            for u in faculty_users:
                last_sub = UserSubscription.objects.filter(
                    user_id=u.id, is_deleted=False
                ).order_by('-created_date').first()
                if not last_sub:
                    logger.warning("No subscription found for faculty user_id=%s; skipping.", u.id)
                    continue

                prev_remaining = (last_sub.remaining_points or Decimal('0'))
                new_remaining  = prev_remaining + amount
                total_points = (last_sub.total_points + amount)
                print(f'total points:{total_points}, prev remain:{prev_remaining}, new remaining:{new_remaining}')
                UserSubscription.objects.create(
                    user_id=u.id,
                    package_id=last_sub.package_id,
                    total_points=total_points,
                    earn_points=amount,
                    remaining_points=new_remaining,
                    created_date=timezone.now(),
                    modified_date=timezone.now(),
                    insert_status='earn',
                    command_name='Bonus Points Added to Faculty (Bulk Update)',
                )
                updated_count += 1

        logger.info("Faculty bulk add complete. Updated %s users.", updated_count)
        return 1 if updated_count > 0 else 0

    # single user path
    if user_id is not None:
        last_sub = UserSubscription.objects.filter(
            user_id=user_id, is_deleted=False
        ).order_by('-created_date').first()
        if not last_sub:
            logger.warning("No subscription found for user_id=%s", user_id)
            return 0

        prev_remaining = (last_sub.remaining_points or Decimal('0'))
        new_remaining = prev_remaining + amount
        total_points = (last_sub.total_points + amount)

        UserSubscription.objects.create(
            user_id=user_id,
            package_id=last_sub.package_id,
            total_points=total_points,
            earn_points=amount,
            remaining_points=new_remaining,
            created_date=timezone.now(),
            modified_date=timezone.now(),
            insert_status='earn',
            command_name='Add New Point',
        )
        logger.info(
            "Added %s points for user_id=%s (Remaining: %s → %s)",
            amount, user_id, prev_remaining, new_remaining
        )
        return 1

    logger.error("Neither user_id nor supported user_type provided.")
    return 0

class UserPointView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        requestdata = request.data
        response_data = {}
        user_subscription_list = []
        Obj = UserSubscription.objects.filter(is_deleted=False, user_id__is_deleted=False,
                                              user_id__is_blocked=False).values_list('user_id', flat=True).distinct(
            'user_id').order_by('-user_id')
        if len(Obj) > 0:
            for i in Obj:
                subscObj = UserSubscription.objects.filter(user_id=i, is_deleted=False).last()
                if subscObj:
                    subscUsedSum = UserSubscription.objects.filter(user_id=i, is_deleted=False).values(
                        'package').annotate(total_used_points=Sum('used_points'))
                    print('&&&&&&&&&&&& Used Points', subscUsedSum[0]['total_used_points'])
                    serializer_data = UserSubscriptionListSerializer(subscObj).data
                    if subscUsedSum:
                        serializer_data['total_used_points'] = subscUsedSum[0]['total_used_points']
                    subscEarnSum = UserSubscription.objects.filter(user_id=i, is_deleted=False).values(
                        'package').annotate(total_earn_points=Sum('earn_points'))
                    if subscEarnSum:
                        serializer_data['total_earn_points'] = subscEarnSum[0]['total_earn_points']
                    user_subscription_list.append(serializer_data)
            response_data['status'] = 1
            # response_data['status1111111'] = list(subscUsedSum)
            response_data['message'] = 'I was able to get the points you used.'
            response_data['data_list'] = user_subscription_list
            # return JsonResponse(response_data, status=200)
            return Response(response_data)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Your point was not used.'
            response_data['utilization'] = []
            return JsonResponse(response_data, status=200)

    # def post(self, request):
    #     requestdata = request.data
    #     response_data = {}
    #
    #     result = point_add(requestdata['user_id'], requestdata['points'])
    #     if result == 1:
    #         response_data['status'] = 1
    #         response_data['message'] = 'Point add successfuly.'
    #         return JsonResponse(response_data, status=200)
    #     else:
    #         response_data['status'] = 0
    #         response_data['message'] = 'Point add failure.'
    #         return JsonResponse(response_data, status=200)
    def post(self, request):
        requestdata = request.data
        user_id   = requestdata.get('user_id')
        points    = requestdata.get('points')
        user_type = requestdata.get('user_type')  # optional: "faculty"

        result = point_add(user_id=user_id, points=points, user_type=user_type)

        if result == 1:
            if user_type == "faculty":
                return JsonResponse({'status': 1, 'message': 'Points added to all faculty.'}, status=200)
            return JsonResponse({'status': 1, 'message': 'Point added successfully.'}, status=200)

        return JsonResponse({'status': 0, 'message': 'Point add failure.'}, status=400)

### User Plan Reports
class UserReportSubscriptionView(APIView):
    def post(self, request):
        requestData = request.data
        user = request.user
        user_email = user.email
        response_data = {}
        data = []
        admin_status = User.objects.filter(email=user_email, is_active=True, is_blocked=False, is_deleted=False).first()
        if admin_status.is_superuser:
            get_plans_details = UserSubscription.objects.filter(user_id=requestData['user_id'], is_deleted=False,
                                                                insert_status='earn').first()
            if get_plans_details:
                serializer = UserSubscriptionSerializer(get_plans_details).data
                qsumearn = UserSubscription.objects.filter(user_id=requestData['user_id'], is_deleted=False,
                                                           insert_status='earn').aggregate(
                    total_earn_points=Sum('earn_points'))
                if qsumearn:
                    serializer['earned_points'] = qsumearn['total_earn_points']
                    serializer['total_points'] = qsumearn['total_earn_points']
                    qs = UserSubscription.objects.filter(user_id=requestData['user_id'], is_deleted=False,
                                                         insert_status='spend').last()
                    if qs:
                        qsum = UserSubscription.objects.filter(user_id=requestData['user_id'], is_deleted=False,
                                                               insert_status='spend').aggregate(
                            total_used_points=Sum('used_points'))
                        if qsum:
                            serializer['used_points'] = qsum['total_used_points']
                            serializer['remaining_points'] = qs.remaining_points
                data.append(serializer)
                response_data['status'] = 1
                response_data['msg'] = "User Plans details"
                response_data['User_plans_details'] = data
                http_status_code = 200
            else:
                response_data['status'] = 0
                response_data['msg'] = 'No Deatils'
                response_data['User_plans_details'] = []
                http_status_code = 404
        else:
            response_data['status'] = 0
            response_data['msg'] = 'you are not admin'
            response_data['User_plans_details'] = []
            http_status_code = 404
        return Response(response_data, status=http_status_code)


class UserReportPointsUsedView(APIView):
    def post(self, request):
        requestData = request.data
        user = request.user
        user_email = user.email
        response_data = {}
        data = []
        admin_status = User.objects.filter(email=user_email, is_active=True, is_blocked=False, is_deleted=False).first()
        if admin_status.is_superuser:
            rs = UserSubscription.objects.filter(user_id=requestData['user_id'], is_deleted=False,
                                                 insert_status='spend').order_by('-id')
            if rs:
                serializer = UserSubscriptionSerializer(rs, many=True)
                response_data['status'] = 1
                response_data['msg'] = 'I was able to get the points you used.'
                response_data['User_points_details'] = serializer.data
                http_status_code = 200
            else:
                response_data['status'] = 0
                response_data['msg'] = 'User point are not used.'
                response_data['User_points_details'] = []
                http_status_code = 400
        else:
            response_data['status'] = 0
            response_data['msg'] = 'you are not admin'
            response_data['User_points_details'] = []
            http_status_code = 404
        return Response(response_data, status=http_status_code)


class SubscriptionView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        response_data = {}
        rs = SubscriptionPackageMaster.objects.filter(is_blocked=False, is_deleted=False)
        if rs:
            serializers = PackageMasterSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Data found successfully.'
            response_data['plans'] = serializers.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'No Plan found.'
            response_data['plans'] = []
            return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        requestdata = request.data
        response_data = {}
        print(requestdata)
        rs = SubscriptionPackageMaster.objects.filter(id=requestdata['plan_id'], is_blocked=False,
                                                      is_deleted=False).first()
        if rs:
            hostname = socket.gethostname()
            IPAddr = socket.gethostbyname(hostname)
            print("Your Computer Name is:" + hostname)
            print("Your Computer IP Address is:" + IPAddr)

            obj = UserSubscription.objects.create(
                user_id=user_id,
                package_id=rs.id,
                total_points=rs.package_points,
                used_points=0,
                remaining_points=rs.package_points,
                package_activation_date=timezone.now(),
                package_deactivation_date=timezone.now() + timezone.timedelta(days=rs.package_duration),
                created_date=timezone.now(),
                modified_date=timezone.now(),
                ipAddress=IPAddr
            )
            print(rs)
            response_data['status'] = 1
            response_data['message'] = 'Insert successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This plan not exist.'
            return JsonResponse(response_data, status=200)

class ExportUserExecutionCSV(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({
                "status": 0,
                "msg": "You are not admin"
            }, status=403)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="v2_user_report.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Name",
            "Username",
            "No. Of Query Fired",
            "Ping Count",
            "DNS Count",
            "Traceroute Count",
            "Points Left",
        ])

        latest_points_subquery = UserSubscription.objects.filter(
            user=OuterRef('pk'),
            is_deleted=False
        ).order_by('-id').values('remaining_points')[:1]

        users = User.objects.filter(
            is_active=True,
            is_deleted=False
        ).annotate(

            total_queries=Count(
                'history_user_id',
                filter=Q(history_user_id__is_deleted=False)
            ),

            ping_count=Count(
                'history_user_id',
                filter=Q(
                    history_user_id__is_deleted=False,
                    history_user_id__query_type__in=[
                        'regular','periodic','domain_anchor_periodic',
                        'domain_zone_regular','domain_zone_periodic','trace'
                    ]
                )
            ),

            dns_count=Count(
                'history_user_id',
                filter=Q(
                    history_user_id__is_deleted=False,
                    history_user_id__query_type='domain_anchor_dns_query'
                )
            ),

            traceroute_count=Count(
                'history_user_id',
                filter=Q(
                    history_user_id__is_deleted=False,
                    history_user_id__query_type__in=[
                        'traceroute','domain_anchor_traceroute','domain_zone_traceroute'
                    ]
                )
            ),

            points_left=Subquery(latest_points_subquery)
        )

        for user in users:
            writer.writerow([
                f"{user.first_name} {user.last_name}".strip(),
                user.username,
                user.total_queries,
                user.ping_count,
                user.dns_count,
                user.traceroute_count,
                user.points_left or 0
            ])

        return response