from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from backend.common.models import Countries, States, Cities
from backend.services_app.anchor_services.get_ip import send_ip_data
from backend.users.models import UserSession
from backend.users.serializers import *
from rest_framework import generics
from rest_framework.response import Response
import base64
from django.utils import timezone
import socket
from backend.subscription.models import SubscriptionPackageMaster, UserSubscription
from django.contrib.auth import get_user_model
from rest_framework.renderers import JSONRenderer
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from services.email_service import EmailHelper


class JSONResponse(HttpResponse):
    """ An HttpResponse that renders its content into JSON. """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        # kwargs['access_control_allow_origin'] = '*'
        super(JSONResponse, self).__init__(content, **kwargs)


class CheckEmailView(generics.ListAPIView):
    lookup_field = 'pk'

    def post(self, request, *args, **kwargs):
        email = request.data['email']
        UserProfile = get_user_model()
        rs = UserProfile.objects.all().filter(email=email, is_deleted="False").first()
        # count = len(rs)
        if rs:
            msg = "Already registered as an user. Use a different email."
            data = {
                'status': 1,
                'error_type': 'email_exist',
                'message': msg
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'error_type': '',
                'message': 'Email Does not Exist',
            }
            return Response(data)


class CheckPhoneView(generics.ListAPIView):
    lookup_field = 'pk'

    def post(self, request, *args, **kwargs):
        phone_no = request.data['phone_no']
        UserProfile = get_user_model()
        count = UserProfile.objects.all().filter(phone_no=phone_no, is_deleted="False").count()
        if count > 0:
            data = {
                'status': 1,
                'error_type': 'phoneno_exist',
                'message': 'Already registered as an user with this number. Use a different number.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'error_type': '',
                'message': 'Phone No Does not Exist',
            }
            return Response(data)


def encode_user_pk(user_pk):
    user_key = base64.b64encode(user_pk)
    return user_key.decode('utf-8')


def assign_default_point(user_id, user_type=None):
    response_data = {}
    rs = SubscriptionPackageMaster.objects.filter(is_default_plan=True, is_blocked=False, is_deleted=False).first()
    if rs:
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        obj = UserSubscription.objects.create(
            user_id=user_id,
            package_id=rs.id,
            total_points=500 if user_type == 'student' else rs.package_points,
            used_points=0,
            remaining_points=500 if user_type == 'student' else rs.package_points,
            earn_points=500 if user_type == 'student' else rs.package_points,
            insert_status='earn',
            package_activation_date=timezone.now(),
            package_deactivation_date=timezone.now() + timezone.timedelta(days=rs.package_duration),
            created_date=timezone.now(),
            modified_date=timezone.now(),
            ipAddress=IPAddr
        )
        response_data['status'] = 1
        response_data['message'] = 'Insert successfully.'
        return response_data
    else:
        response_data['status'] = 0
        response_data['message'] = 'This plan not exist.'
        return response_data


def recharge_user_points(user_id, recharge_points, command_name=None, run_time=None):
    response_data = {}

    try:
        subscription = UserSubscription.objects.filter(user_id=user_id, is_deleted=False).last()

        if not subscription:
            response_data['status'] = 0
            response_data['message'] = 'No active subscription found for this user.'
            return JsonResponse(response_data, status=400)

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        new_remaining_points = subscription.remaining_points + recharge_points
        new_total_earn_points = subscription.earn_points + recharge_points

        with transaction.atomic():
            # Insert a new record for the recharge (earn)
            UserSubscription.objects.create(
                user_id=user_id,
                package_id=subscription.package_id,
                total_points=subscription.total_points,
                used_points=0,
                earn_points=recharge_points,
                remaining_points=new_remaining_points,
                package_activation_date=subscription.package_activation_date,
                package_deactivation_date=subscription.package_deactivation_date,
                created_date=timezone.now(),
                modified_date=timezone.now(),
                insert_status='earn',
                command_name=command_name,
                run_time=run_time,
                ipAddress=ip_address
            )

        response_data['status'] = 1
        response_data['message'] = 'Points recharged successfully.'
        return JsonResponse(response_data, status=200)

    except Exception as e:
        response_data['status'] = 0
        response_data['message'] = f'Error occurred during recharge: {str(e)}'
        return JsonResponse(response_data, status=500)


class UserRegistrationView(generics.ListAPIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        try:
            if serializer.is_valid():
                requestData = serializer.validated_data
                print("request.....................................", requestData)

                email = requestData.get('email', '')
                username = email
                password = requestData.get('password', '')
                phone_no = requestData.get('phone_no', '')
                first_name = requestData.get('first_name', '')
                last_name = requestData.get('last_name', '')
                designation = requestData.get('designation', '')
                company_name = requestData.get('company_name', '')
                is_faculty = requestData.get('is_faculty', '')
                institution_name = requestData.get('institution_name', '')
                address = requestData.get('address', '')
                pin_code = requestData.get('pin_code', '')
                city = requestData.get('city', '')
                country = requestData.get('country', '')
                state = requestData.get('state', '')
                is_phone_verified = requestData.get('is_phone_verified', '')
                is_email_verified = requestData.get('is_email_verified', '')
                user_pk = encode_user_pk(bytes(password or '', 'utf-8'))
                ## check Emai aiiready exist or not
                user = User.objects.filter(email=email, is_deleted=False).count()

                # Fetch and validate country
                if country:
                    country_obj = Countries.objects.filter(id=country).first()
                    if not country_obj:
                        return JsonResponse({'status': 0, 'message': 'Invalid country name'}, status=400)
                else:
                    country_obj = None

                # Fetch and validate state
                if state:
                    state_obj = States.objects.filter(id=state).first()
                    if not state_obj:
                        return JsonResponse({'status': 0, 'message': 'Invalid state name for the selected country'},
                                            status=400)
                else:
                    state_obj = None

                # Fetch and validate city
                if city:
                    city_obj = Cities.objects.filter(id=city).first()
                    if not city_obj:
                        return JsonResponse({'status': 0, 'message': 'Invalid city name for the selected state'},
                                            status=400)
                else:
                    city_obj = None

                if user > 0:
                    msg = {"Unauthorized error ": ['Email already exists.', ]}
                    # msg = 'User with this email already exists.'
                    errors = {'errors': msg}
                    return JSONResponse(errors, status=401)
                else:
                    obj = User.objects.create_user(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone_no=phone_no,
                        username=username,
                        designation=designation,
                        company_name=company_name,
                        institution_name=institution_name,
                        address=address,
                        pin_code=pin_code,
                        country=country_obj,
                        city=city_obj,
                        state=state_obj,
                        created_date=timezone.now(),
                        modified_date=timezone.now(),
                        is_staff=False,
                        is_superuser=False,
                        is_phone_verified=is_phone_verified == 'valid',
                        is_email_verified=is_email_verified == 'valid',
                        is_active=True,
                        is_faculty=is_faculty,
                        user_pk=user_pk
                    )
                    obj.set_password(password)
                    obj.save()
                    assign_points_response = assign_default_point(obj.id)
                    # print('assign_points_response', assign_points_response)

                    response_msg = 'User created successfully.'
                    # Sending a welcome email
                    email_helper = EmailHelper(user=obj, email_type='welcome')
                    email_status = email_helper.send_email()
                    if email_status['status'] == 'success':
                        response_msg += ' A welcome email has been sent.'
                    else:
                        response_msg += ' Failed to send welcome email.'

                    return JSONResponse({
                        'status': 1,
                        'id': obj.id,
                        'email': obj.email,
                        'username': obj.username,
                        'designation': obj.designation,
                        'message': response_msg
                    }, status=200)
            else:
                return JSONResponse({'message': 'Please fill all required data!'}, status=400)
        except Exception as e:
            print("ERROR>.................................", e)
            return JsonResponse({'msg': e}, status=401)


class UserSessionView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def post(self, request):
        """Create or update user session."""
        user = request.user
        lat = request.data.get('lat')
        long = request.data.get('long')
        public_ip = request.data.get('public_ip')
        location = request.data.get('location')
        isp_details = request.data.get('isp_details')

        user_session = UserSession.objects.create(
            user=user,
            lat=lat,
            long=long,
            public_ip=public_ip,
            location=location if location else None,
            isp_details=isp_details if isp_details else None,
            last_login=timezone.now()
        )

        return Response({
            'message': 'User session created/updated successfully',
            'session_id': user_session.id,
            'last_login': user_session.last_login,
        }, status=status.HTTP_200_OK)

    def get(self, request):
        """Retrieve user session."""
        user = request.user
        print("user data...........", user.id)
        try:
            user_session = UserSession.objects.get(user=user)
            return Response({
                'user_id': user.id,
                'lat': user_session.lat,
                'long': user_session.long,
                'public_ip': user_session.public_ip,
                'location': user_session.location,
                'isp_details': user_session.isp_details,
                'last_login': user_session.last_login,
            }, status=status.HTTP_200_OK)
        except UserSession.DoesNotExist:
            return Response({'error': 'User session not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        """Delete user session."""
        user = request.user
        try:
            user_session = UserSession.objects.get(user=user)
            user_session.delete()
            return Response({'message': 'User session deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except UserSession.DoesNotExist:
            return Response({'error': 'User session not found'}, status=status.HTTP_404_NOT_FOUND)


# Not using anymore 10-06-2025
class UserLoginView(generics.ListAPIView):
    # permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            requestData = serializer.validated_data
            email = requestData['email']
            password = requestData['password']
            User = get_user_model()
            try:  ## Check user Email Exist
                user = User.objects.filter(email=email, is_deleted=False, is_blocked=False).first()
                if user:
                    if user.check_password(password):  ## Check password matched or not
                        if user.is_email_verified:  ## Check user email is varified or not
                            if user.is_active:  ## Check user active or deactive
                                token, created = Token.objects.get_or_create(
                                    user=user)  ### Get user authentication token
                                token_data = token.key  ### if it is first login then create token first and get token
                                user.last_login = timezone.now()
                                user.save()
                                # return_ip = get_ip()
                                return_ip = '47.15.40.115'

                                serialize_userdata = {
                                    'status': 1,
                                    'id': user.id,
                                    'email': user.email,
                                    'username': user.username,
                                    'token': token_data,
                                    'first_name': user.first_name,
                                    'last_name': user.last_name,
                                    'is_superuser': user.is_superuser,
                                    'is_active': user.is_active,
                                    'is_staff': user.is_staff,
                                    'last_login': user.last_login,
                                    'user_public_ip': return_ip
                                }
                                return JSONResponse(serialize_userdata, status=200)
                            else:
                                return JSONResponse({'status': 0, 'msg': 'Your account is not activated.'}, status=200)
                        else:
                            return JsonResponse({'status': 2, 'id': user.id, 'msg': 'Your email is not verified'},
                                                status=200)
                    else:
                        return JsonResponse({'status': 0, 'msg': 'Password did not match'}, status=200)
                else:
                    return JsonResponse({'status': 0, 'msg': 'Email did not match'}, status=200)
            except User.DoesNotExist:
                return JSONResponse({'status': 0, 'msg': 'Authentication Error'}, status=401)
        else:
            return JsonResponse({'msg': 'Email Or Password did not match'}, status=401)


class UserListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        response_data = {}
        qs = CustomUser.objects.filter(is_deleted=False, is_superuser=False).order_by('-id')

        if qs.count() > 0:
            serializer = UsersSerializer(qs, many=True)
            response_data['status'] = 1
            response_data['message'] = 'Data found successfully'
            response_data['users'] = serializer.data
        else:
            response_data['status'] = 0
            response_data['message'] = 'Data not found'
            response_data['users'] = []
        return Response(response_data, status=200)

    def put(self, request):
        user = request.user
        user_id = user.id
        data = {}
        response_data = {}
        requestdata = request.data
        is_blocked = request.data.get('is_blocked', None)
        is_deleted = request.data.get('is_deleted', None)

        qscount = CustomUser.objects.filter(is_deleted=False, pk=request.data['user_id']).count()
        if qscount > 0:
            obj = CustomUser.objects.filter(pk=request.data['user_id'])
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
            data = {
                'status': 1,
                'api_status': 1,
                'message': 'User update successfully.',
            }
            return Response(data)
        else:
            data = {
                'status': 0,
                'api_status': 0,
                'message': 'This user is not exist.',
            }
            return Response(data)


def decode_user_pk(user_pk):
    user_key = base64.b64decode(bytes(user_pk, 'utf-8'))
    return user_key.decode('utf-8')


class AdminUserLogin(generics.ListAPIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        try:
            request_user = User.objects.filter(email=request.user, is_deleted=False, is_blocked=False).first()
            if request_user.is_superuser:
                get_user_det = User.objects.filter(id=user_id, is_deleted=False, is_blocked=False).first()
                if get_user_det.is_email_verified:  ## Check user email is varified or not
                    if get_user_det.is_active:  ## Check user active or deactive
                        if get_user_det.user_pk:
                            user_pk = decode_user_pk(get_user_det.user_pk)
                            token, created = Token.objects.get_or_create(
                                user=get_user_det)  ### Get user authentication token
                            token_data = token.key  ### if it is first login then create token first and get token
                            get_user_det.last_login = timezone.now()
                            get_user_det.save()
                            serialize_userdata = {
                                'status': 1,
                                'id': get_user_det.id,
                                'email': get_user_det.email,
                                'username': get_user_det.username,
                                'token': token_data,
                                'first_name': get_user_det.first_name,
                                'last_name': get_user_det.last_name,
                                'is_superuser': get_user_det.is_superuser,
                                'is_active': get_user_det.is_active,
                                'is_staff': get_user_det.is_staff,
                                'last_login': get_user_det.last_login,
                                'user_pk': user_pk
                            }
                            return JSONResponse(serialize_userdata, status=200)
                        else:
                            return JSONResponse({'status': 0, 'msg': 'Cannot Have Access'}, status=200)
                    else:
                        return JSONResponse({'status': 0, 'msg': 'User is not acivated.'}, status=200)
                else:
                    return JsonResponse({'status': 2, 'id': get_user_det.id, 'msg': 'User email is not verified'},
                                        status=200)
            else:
                return JsonResponse({'status': 3, 'id': request_user.id, 'msg': 'You are not admin'}, status=200)
        except User.DoesNotExist:
            return JSONResponse({'status': 0, 'msg': 'Authentication Error'}, status=400)


class UserChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        data = request.data
        old_password = data.get('oldpassword')
        new_password = data.get('newpassword')

        if not old_password or not new_password:
            return JsonResponse({'status': 0, 'msg': 'Both old and new password are required.'}, status=400)

        if not user.check_password(old_password):
            return JsonResponse({'status': 0, 'msg': 'Old password is incorrect.'}, status=400)

        user.set_password(new_password)
        user.save()

        # Update the user_pk (custom logic)
        encoded_pk = encode_user_pk(new_password.encode('utf-8'))
        user.user_pk = encoded_pk
        user.save(update_fields=['user_pk'])

        return JsonResponse({'status': 1, 'msg': 'Password changed successfully.'}, status=200)
