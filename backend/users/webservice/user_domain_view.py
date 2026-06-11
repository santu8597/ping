from rest_framework.response import Response
from django.http import JsonResponse
from backend.users.serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone






class DomainView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        rs = UsersDomain.objects.filter(user_id=user_id, is_deleted=False).order_by('-id')
        if rs:
            serializer = DomainViewSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Domain list.'
            response_data['domain'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Domain list blank.'
            response_data['domain'] = []
            return JsonResponse(response_data, status=200)

    # def post(self, request):
    #     user = request.user
    #     user_id = user.id
    #     response_data = {}
    #     requestData = request.data
    #     domain_ip = requestData['ip']
    #     if user:
    #         obj = UsersDomain.objects.create(
    #             user_id=user_id,
    #             domain_name=requestData['domain_name'],
    #             domain_ip=domain_ip,
    #             created_date=timezone.now(),
    #             modified_date=timezone.now(),
    #         )
    #         response_data['status'] = 1
    #         response_data['obj_id'] = obj.id
    #         response_data['message'] = 'Domain save successfully.'
    #         return JsonResponse(response_data, status=200)
    #     else:
    #         response_data['status'] = 0
    #         response_data['message'] = 'Domain save failure.'
    #         return JsonResponse(response_data, status=200)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data

        domain_ip = requestData.get('ip')
        domain_name = requestData.get('domain_name')

        #  Validate domain existence
        if validate_domain_exists(domain_ip, user_id):
            response_data['status'] = 0
            response_data['message'] = 'Domain already exists!'
            return JsonResponse(response_data, status=200)

        if user:
            obj = UsersDomain.objects.create(
                user_id=user_id,
                domain_name=domain_name,
                domain_ip=domain_ip,
                created_date=timezone.now(),
                modified_date=timezone.now(),
            )
            response_data['status'] = 1
            response_data['obj_id'] = obj.id
            response_data['message'] = 'Domain saved successfully.'
            return JsonResponse(response_data, status=200)

        response_data['status'] = 0
        response_data['message'] = 'Domain save failure.'
        return JsonResponse(response_data, status=200)

    def put(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        is_delete = request.data.get('is_delete', None)
        requestData = request.data
        rs = UsersDomain.objects.filter(user_id=user_id, id=requestData['domain_id'])
        if rs:
            if is_delete is not None:
                UsersDomain.objects.filter(id=requestData['domain_id']).update(is_deleted=is_delete,
                                                                               modified_date=timezone.now())
            else:
                UsersDomain.objects.filter(id=requestData['domain_id']).update(domain_name=requestData['domain_name'],
                                                                               domain_ip=requestData['ip'],
                                                                               modified_date=timezone.now())
            response_data['status'] = 1
            response_data['message'] = 'Domain update successfully.'
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'Domain update failure.'
            return JsonResponse(response_data, status=200)


class DomainDetailsView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_id = user.id
        response_data = {}
        requestData = request.data
        rs = UsersDomain.objects.filter(user_id=user_id, id=requestData['domain_id'], is_deleted=False)
        if rs:
            serializer = DomainViewSerializer(rs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Domain details'
            response_data['domain'] = serializer.data
            return JsonResponse(response_data, status=200)
        else:
            response_data['status'] = 0
            response_data['message'] = 'This domain is not present in our database'
            response_data['domain'] = []
            return JsonResponse(response_data, status=200)


class UserReportDomainView(APIView):

    def post(self, request):
        requestData = request.data
        user = request.user
        user_email = user.email
        response_data = {}
        admin_status = User.objects.filter(email=user_email, is_active=True, is_blocked=False, is_deleted=False).first()
        if admin_status.is_superuser:
            get_domain_details = UsersDomain.objects.filter(user_id=requestData['user_id'], is_blocked=False,
                                                            is_deleted=False)
            if get_domain_details:
                serializer = UserReportDomainDetSerializer(get_domain_details, many=True)
                response_data['status'] = 1
                response_data['msg'] = "User Domain details"
                response_data['User_domain_details'] = serializer.data
                http_status_code = 200
            else:
                response_data['status'] = 0
                response_data['msg'] = 'No Domain Deatils'
                response_data['User_domain_details'] = []
                http_status_code = 404
        else:
            response_data['status'] = 0
            response_data['msg'] = 'you are not admin'
            response_data['User_domain_details'] = []
            http_status_code = 404
        return Response(response_data, status=http_status_code)


def validate_domain_exists(domain_ip: str, user_id: str) -> bool:
    """Check if a domain with the given IP already exists (not deleted)."""
    print("dOMAIN HERE", domain_ip, UsersDomain.objects.filter(domain_ip=domain_ip).exists())
    return UsersDomain.objects.filter(domain_ip=domain_ip, user_id=user_id, is_deleted=False).exists()