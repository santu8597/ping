import csv
import json
import os
try:
    import pandas as pd
except Exception:
    pd = None
    print("pandas import failed; CSV features disabled")
import requests
from django.conf import settings
from django.contrib import auth, messages
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from dotenv import load_dotenv
from backend.utils.helpers import delete_cache
from backend.services_app.anchor_services.anchor import AnchorQueries
from backend.services_app.anchor_services.assignment import AssignmentServices
from backend.services_app.anchor_services.domain import DomainServices
from backend.services_app.anchor_services.get_ip import send_ip_data
from backend.services_app.anchor_services.points import SubsciptionServices
from backend.services_app.anchor_services.profile import ProfileServices
from backend.services_app.anchor_services.students import StudentServices
from backend.services_app.anchor_services.zone import ZoneServices
from backend.services_app.common import (get_cities, get_countries,
                                         get_point_details,
                                         get_profile_details,
                                         get_remaining_points_by_user,
                                         get_states, token_required)
from config_env import CONFIG
from django.views.decorators.http import require_POST
from django.utils.timezone import now
import pytz
# from views import add_point


load_dotenv()
# Create your views here.
api_prefix_viz = CONFIG.API_URL_VIZ
api_prefix_rd3 = CONFIG.API_URL_RD3
key_api = CONFIG.APIKEY

@token_required
def dashboard(request):
    try:
        token = request.token

        profile_data = get_profile_details(token)
        profile_detail = {
            "first_name": profile_data.get("data").get("first_name"),
            "last_name": profile_data.get("data").get("last_name"),
            "designation": profile_data.get("data").get("designation", ""),
            "is_student": profile_data.get("data").get("is_student"),
            "is_faculty": profile_data.get("data").get("is_faculty"),
            "profile_image": profile_data.get("data").get("profile_image", ""),
            "userid": profile_data.get("data").get("id", "")
        }
        request.session["profile_detail"] = profile_detail

        points_data = get_point_details(token)
        # print("get data..................", profile_detail)
        # print("get point..................", points_data)
        try:
            response_ip = send_ip_data(request) or {}
        except Exception as e:
            print("No IP", e)
            response_ip = {}

        ip_address = response_ip.get('data', {}).get('ip', "0.0.0.0")
        request.session["ip_address"] = ip_address

        # discussion feature disabled: do not call external discussion APIs
        response_discussion_data = {"categories": []}
        anchor_queries = AnchorQueries(token)
        online_anchors = anchor_queries.get_online_anchors()
        subscription_data = SubsciptionServices(token)
        response_subscription_data = subscription_data.get_subscription_data()
        # Absolute path to CSV
        csv_path = os.path.join(settings.BASE_DIR, 'static', 'services_app/external_files',
                                'top_200_in_domains_with_ips.csv')

        if pd:
            try:
                df = pd.read_csv(csv_path)
                data = df.to_dict(orient='records')  # [{'col1': val1, 'col2': val2}, ...]
                headers = list(df.columns)
            except Exception as e:
                # Debugging output if something goes wrong
                print(f"Error reading CSV: {e}")
                data = []
                headers = []
        else:
            data = []
            headers = []

    except:
        messages.error(request, "Invalid Password or Username!")
        return redirect('services_app:index')
    return render(request, 'services_app/index.html',
                  {"user_data": profile_data["data"], "user_point": points_data["data"],
                   "anchor_list": online_anchors.get('anchor', []),
                   # discussion_data removed
                   "subscription_data": response_subscription_data["plans"][0],
                   'csv_data': data,
                   'headers': headers, 'server_data': response_ip.get('data', ''), "api_prefix_viz": api_prefix_viz})


def index(request):
    return render(request, 'services_app/auth-login.html')


def user_login(request):
    username = request.POST.get("user")
    password = request.POST.get("user_pass")
    payload = {
        "username": username,
        "password": password
    }

    check_response = requests.post(api_prefix_viz + "/api/user/email/verify/", json={"username": username})
    check_data = check_response.json()

    if not check_data.get("email_verified", False):
        messages.error(request, check_data.get("detail", "Email verification check failed."))
        return redirect("services_app:dashboard")

    # print(api_prefix_viz, password)
    response = requests.post(api_prefix_viz + "/api/token/", data=payload)

    response_data = response.json()
    # print(response_data)

    if response.status_code == 200:

        token = response_data["access"]
        request.session["token"] = token

        long = request.POST.get("long")
        lat = request.POST.get("lat")
        try:
            response_ip = send_ip_data(request) or {}
        except Exception as e:
            print("No IP", e)
            response_ip = {}

        ip_address = response_ip.get('data', {}).get('ip', "0.0.0.0")
        accessing_from = response_ip.get('data', {}).get('address', "Not Found")
        org = response_ip.get('data', {}).get('org', "Not Found")
        header = {'Authorization': f'Bearer {token}'}
        session_payload = {
            "lat": float(lat) if lat else None,
            "long": float(long) if long else None,
            "public_ip": ip_address,
            "location": accessing_from,
            "isp_details": org
        }
        # print("session payload......", session_payload)
        session_response = requests.post(api_prefix_viz + "/api/user/session/", data=session_payload, headers=header)

        session_response_data = session_response.json()
        # print("session response data.........", session_response_data)
        if session_response.status_code == 200:
            print("Session Logged", session_response_data['message'])
        else:
            print("Session Logging Failed", session_response_data['message'])

        return redirect('services_app:dashboard')

    else:
        messages.error(request, "Invalid Password or Username!")
        return redirect('services_app:index')


def logout(request):
    request.session.flush()  # clears custom session data like 'token'
    messages.success(request, "Logged out successfully.")
    return redirect('services_app:index')


def register(request):
    countries = get_countries()
    cities = get_cities()
    states = get_states()
    return render(request, 'services_app/auth-register.html',
                  {"countries": countries["countries"], "cities": cities["cities"], "states": states["states"]})


def get_registration(request):
    """User & Faculty Login"""
    role = request.POST.get("role")
    password = request.POST.get("password")
    email = request.POST.get("email")
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    mobile = request.POST.get("mobile")
    institution_name = request.POST.get("institute")
    address = request.POST.get("address")
    country = request.POST.get("country")
    state = request.POST.get("state")
    city = request.POST.get("city")

    pin_code = request.POST.get("pincode")
    designation = request.POST.get("designation")
    company = request.POST.get("company")
    email_status = request.POST.get('email_status')
    mobile_status = request.POST.get('mobile_status')
    is_faculty = True if role == "faculty" else False
    payload = {
        "password": password,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone_no": mobile,
        "designation": designation,
        "is_faculty": is_faculty,
        "institution_name": institution_name,
        "address": address,
        "pin_code": pin_code,
        "company_name": company,
        "country": country,
        "state": state,
        "city": city,
        "is_email_verified": email_status,
        "is_phone_verified": mobile_status

    }
    # print("registration,,,,", payload)

    response = requests.post(api_prefix_viz + "/api/user/registration/", data=payload)

    response_data = response.json()
    # print(response_data)
    if response.status_code == 200:

        return JsonResponse({"status": 1, "msg": response_data['message']})

    else:
        messages.error(request, "Invalid Password or Username!")
        return redirect('services_app:index')


def forgot_password(request):
    return render(request, 'services_app/auth-recover-pw.html')


def forgot_password_generation(request):
    email = request.POST.get('user_email')
    payload = {"email": email}
    response = requests.post(api_prefix_viz + "/api/user/forgot/password/", data=payload)
    response_data = response.json()
    if response.status_code == 200:
        messages.success(
            request, response_data['message'])
    else:
        messages.error(request, "Invalid Email!")
        return redirect('services_app:forgot_password')
    return render(request, 'services_app/auth-recover-pw.html')


@token_required
def faculty_reset_student_password(request):
    '''Faculty sends reset password link to student'''
    email = request.POST.get('user_email')
    payload = {"email": email}
    response = requests.post(api_prefix_viz + "/api/user/forgot/password/", data=payload)
    response_data = response.json()
    if response.status_code == 200:

        return JsonResponse({"status": 1, "msg": response_data.get('message', 'Reset link sent to registered email')})
    else:
        return JsonResponse({"status": 0, "msg": response_data.get('message', 'Failed to send reset password link ')})


@token_required
def profile(request):
    token = request.token
    profile_data = get_profile_details(token)
    points_data = get_point_details(token)
    countries = get_countries()
    cities = get_cities()
    states = get_states()
    subscription_data = SubsciptionServices(token)
    ip = request.session.get('ip_address')
    response_subscription_data = subscription_data.get_subscription_data()
    point_utilization_data = subscription_data.get_point_utilization_data()
    point_utilization = point_utilization_data["utilization"]
    return render(request, 'services_app/profile.html',
                  {"user_data": profile_data["data"], "user_point": points_data["data"],
                   "subscription_data": response_subscription_data["plans"][0], "point_utilization": point_utilization,
                   "countries": countries["countries"], "states": states["states"], "cities": cities["cities"],
                   "token": token, 'ip': ip})


@token_required
def update_profile(request):
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    mobile = request.POST.get("mobile")
    institution_name = request.POST.get("institute")
    address = request.POST.get("address")
    country = request.POST.get("country")
    state = request.POST.get("state")
    city = request.POST.get("city")
    pin_code = request.POST.get("pincode")
    designation = request.POST.get("designation")
    company = request.POST.get("company")
    linkedin_url = request.POST.get("linkedin_link")
    github_url = request.POST.get("github_link")
    hndb_url = request.POST.get("hndb_link")
    img_path = request.POST.get("img_path")
    is_student = request.POST.get("is_student") == "true"
    is_faculty = request.POST.get("is_faculty") == "true"

    token = request.token
    header = {'Authorization': f'Bearer {token}'}
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "phone_no": mobile,
        "designation": designation,
        "institution_name": institution_name,
        "address": address,
        "pin_code": pin_code,
        "company_name": company,
        "country": country,
        "state": state,
        "city": city,
        "github_url": github_url,
        "hndb_url": hndb_url,
        "linkedin_url": linkedin_url
    }
    # print("update payload,,,,", payload)

    response = requests.patch(api_prefix_viz + "/api/user/profile-details/", data=payload, headers=header)

    response_data = response.json()
    # print(response_data)

    if response.status_code == 200:
        profile_detail = {
            "first_name": first_name,
            "last_name": last_name,
            "designation": designation,
            "is_student": is_student,
            "is_faculty": is_faculty,
            "profile_image": img_path
        }
        request.session["profile_detail"] = profile_detail

        return JsonResponse({"status": 1, "msg": response_data.get('message', 'Profile updated')})
    else:
        return JsonResponse({"status": 0, "msg": response_data.get('message', 'Profile Updation failed')})


@token_required
def upload_profile_image(request):
    token = request.token
    header = {'Authorization': f'Bearer {token}'}
    if request.method == "POST":
        image_file = request.FILES.get("profile_image")
        if not image_file:
            return JsonResponse({"status": 0, "msg": "No image file uploaded."}, status=400)

        try:

            files = {"profile_image": image_file}

            response = requests.post(
                request.build_absolute_uri("/api/user/upload/profile-image/"),
                headers=header,
                files=files
            )

            if response.status_code == 200:
                return JsonResponse({"status": 1, "msg": "Image uploaded successfully.", "data": response.json()})
            else:
                return JsonResponse({"status": 0, "msg": response.json().get("msg", "Upload failed.")})

        except Exception as e:
            return JsonResponse({"status": 0, "msg": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"status": 0, "msg": "Invalid request method."}, status=405)


@token_required
def change_profile_password(request):
    old_password = request.POST.get("password_old")
    password_new = request.POST.get("password_new")

    token = request.token
    header = {'Authorization': f'Bearer {token}'}
    payload = {
        "oldpassword": old_password,
        "newpassword": password_new
    }
    response = requests.post(api_prefix_viz + "/api/user/change-password/", data=payload, headers=header)
    response_data = response.json()

    if response.status_code == 200:
        return JsonResponse({"status": 1, "msg": response_data.get('msg', 'Password updated')})
    else:
        return JsonResponse({"status": 0, "msg": response_data.get('msg', 'Failed to change password')})


@token_required
def discussion(request):
    # Discussion page disabled
    return render(request, 'services_app/feature_removed.html', {"feature": "Discussion Forum"})


@token_required
def get_discussions(request, cat_id):
    return JsonResponse({"status": 0, "msg": "Discussions feature disabled."}, status=410)

@token_required
def get_ai_summary(request, cat_id):
    return JsonResponse({"status": 0, "msg": "AI summary (discussions) disabled."}, status=410)


@require_POST
@token_required
def vote_discussion(request, discussion_id):
    return JsonResponse({"status": 0, "msg": "Voting disabled (discussions removed)."}, status=410)


@require_POST
@token_required
def vote_reply(request, reply_id):
    return JsonResponse({"status": 0, "msg": "Voting disabled (discussions removed)."}, status=410)


@token_required
def add_topic(request):
    return JsonResponse({"status": 0, "msg": "Adding topics disabled."}, status=410)


@token_required
def add_discussion(request):
    return JsonResponse({"status": 0, "msg": "Adding discussions disabled."}, status=410)

@method_decorator(token_required, name='dispatch')
class DomainView(View):
    def get(self, request, *args, **kwargs):
        token = request.token
        domain_service = DomainServices(token)
        domain_data = domain_service.get_domain_data()
        ip = request.session.get('ip_address')
        user_data = request.session.get("profile_detail")
        return render(request, 'services_app/domain.html',
                      {"domain_data": domain_data['domain'], "user_data": user_data,
                       "time_diff": domain_data.get('time_diff', ''), 'ip': ip})

    def post(self, request, *args, **kwargs):
        token = request.token
        action_type = request.POST.get("action_type")

        domain_service = DomainServices(token)
        if action_type == "add_domain":
            domain = request.POST.get("domain")
            ip = request.POST.get("ip")
            return JsonResponse(
                domain_service.add_domain_data(domain_name=domain, domain_ip=ip)
            )

        elif action_type == "edit_domain":
            domain_id = request.POST.get("domain_id")
            domain = request.POST.get("domain")
            ip = request.POST.get("ip")
            return JsonResponse(
                domain_service.edit_domain_data(domain_id=domain_id, new_domain=domain, new_ip=ip)
            )

        elif action_type == "delete_domain":
            domain_id = request.POST.get("domain_id")
            return JsonResponse(domain_service.delete_domain_data(domain_id=domain_id))

        elif action_type == "admin_report_domain":
            user_id = request.POST.get("user_id")
            return JsonResponse(domain_service.get_domain_report_data(user_id=user_id))

        # fallback
        return JsonResponse({"status": 0, "message": "Invalid action type"})


@method_decorator(token_required, name='dispatch')
class ZoneView(View):
    def get(self, request, *args, **kwargs):
        # Only return the token if it's an API call
        if request.GET.get('token') == 'true':
            # print(f"token:{request.token}")
            return JsonResponse({"token": request.token})

        # Otherwise render the page, always include time for rendering
        token = request.token
        zone_service = ZoneServices(token)
        zone_data = zone_service.get_zone_data(include_time=True)  # Always include time here

        anchor_queries = AnchorQueries(token)
        online_anchors = anchor_queries.get_online_anchors()
        user_data = request.session.get("profile_detail")
        ip = request.session.get('ip_address')
        return render(request, 'services_app/zone.html',
                      {"zone_data": zone_data.get("zone_data") or zone_data.get("zone", []),
                       "anchor_list": online_anchors.get('anchor', []),
                       "user_data": user_data, "time_diff": zone_data.get("time_diff", ""),
                       'ip': ip, "api_prefix_viz": api_prefix_viz})

    def post(self, request, *args, **kwargs):
        token = request.token
        anchor_ids = request.POST.getlist("anchor_list")
        zone_name = request.POST.get("zone")
        zone_service = ZoneServices(token)
        zone_data = zone_service.add_zone_data(anchor_ids=anchor_ids, zone=zone_name)
        return JsonResponse(zone_data)

    def put(self, request, *args, **kwargs):
        token = request.token
        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"status": 0, "message": "Invalid JSON"}, status=400)

        zone_id = body.get("zone_id")
        if not zone_id:
            return JsonResponse({"status": 0, "message": "Missing zone_id"}, status=400)

        zone_service = ZoneServices(token)
        response = zone_service.delete_zone_data(zone_id=zone_id)
        return JsonResponse(response)


@token_required
def anchor(request):
    # Anchor management UI removed — render feature-removed page instead (non-destructive)
    user_data = request.session.get("profile_detail")
    return render(request, 'services_app/feature_removed.html', {"feature": "Anchor Management - Anchors",
                                                                   "user_data": user_data})


@token_required
def anchor_removed(request):
    # Backwards-compatible stub for routes expecting `anchor_removed`
    user_data = request.session.get("profile_detail")
    return render(request, 'services_app/feature_removed.html', {"feature": "Anchor Management - Anchors",
                                                                   "user_data": user_data})


@token_required
def register_anchor_page(request):
    # Anchor registration UI removed — render feature-removed page instead (non-destructive)
    user_data = request.session.get("profile_detail")
    return render(request, 'services_app/feature_removed.html', {"feature": "Anchor Management - Registration",
                                                                   "user_data": user_data})


@token_required
def user_anchor_registration(request):
    # Anchor registration endpoint removed — return 410 Gone for API consumers
    return JsonResponse({"status": 0, "msg": "Anchor registration feature removed"}, status=410)


@token_required
def user_anchor_registration_removed(request):
    # Backwards-compatible alias for removed registration endpoint
    return JsonResponse({"status": 0, "msg": "Anchor registration feature removed"}, status=410)


@token_required
def user_anchor_update_location(request):
    # Anchor location update API removed — return 410 Gone
    return JsonResponse({"status": 0, "msg": "Anchor update feature removed"}, status=410)


@token_required
def user_anchor_update_location_removed(request):
    # Backwards-compatible alias for removed update endpoint
    return JsonResponse({"status": 0, "msg": "Anchor update feature removed"}, status=410)


@token_required
def ping_command_page(request):
    token = request.token
    domain_service = DomainServices(token)
    domain_data = domain_service.get_domain_data()
    anchor_queries = AnchorQueries(token)
    online_anchors = anchor_queries.get_online_anchors()
    zone_queries = ZoneServices(token)
    zone_data = zone_queries.get_zone_data()
    user_data = request.session.get("profile_detail")
    ip = request.session.get('ip_address')
    return render(request, 'services_app/ping_command.html', {"domain_data": domain_data['domain'],
                                                              "anchor_list": online_anchors['anchor'],
                                                              "zone_list": zone_data['zone'],
                                                              "user_data": user_data,
                                                              'ip': ip, "api_prefix_viz": api_prefix_viz,
                                                              "token": token})


@token_required
def generate_ping_query(request):
    domain = request.POST.get("domain")
    query_type = request.POST.get("query_type")
    anchor_data = request.POST.get("anchor")
    interval_unit = request.POST.get("interval_unit")
    interval_time = request.POST.get("interval_time")
    time_unit = request.POST.get("time_unit")
    time = request.POST.get("time")
    zone = request.POST.get("zone")
    print("zone.....", zone)

    key_api = os.getenv('APIKEY')
    token = request.token
    header = {'Authorization': f'Bearer {token}'}
    dataset_list = []

    # Handle anchor_data
    if anchor_data:
        parts = anchor_data.split(",", 4)
        if len(parts) == 5:
            anchor_id, anchor_location, anchor_anchor_id, anchor_lease_id, user_id = parts
        else:
            anchor_id = anchor_location = anchor_anchor_id = anchor_lease_id = user_id = None
    else:
        anchor_id = anchor_location = anchor_anchor_id = anchor_lease_id = user_id = None

    # CASE 1: Periodic query without zone
    if query_type == "periodic" and not zone:
        point_fix = {
            "anchor_user_id": int(user_id),
            "anchor_user_ids": [],
            "command_name": "ping",
            "run_time": 10,
            "utilize_point": 5
        }
        # print("Step 1 points periodic payload........", point_fix)
        response_point = requests.post(api_prefix_viz + "/api/subscription/point-utilization/", headers=header,
                                       json=point_fix)
        response_point_data = response_point.json()
        # print("Step 1 points periodic........", response_point_data)

        if response_point.status_code == 200:
            fixed_data = {
                "cmd_value": "ping",
                "cmd_type": "periodic",
                "host_id": domain,
                "interval_time": int(interval_time),
                "interval_unit": interval_unit,
                "query_status": "enqueue",
                "anchor_id": [anchor_id],
                "time_unit": time_unit,
                "run_time": int(time),
                "run_count": "3",
                "service_ids": [domain],
                "type_fo_query": "domain_anchor_periodic",
                "zone_id": []
            }
            print("Step 2 periodic payload........", fixed_data)
            response = requests.post(api_prefix_viz + "/api/anchor/preiodic-command-history-with-anchor-or-zone/",
                                     headers=header, json=fixed_data)
            response_data = response.json()
            # print("Step 2 periodic........", response_data)
            return JsonResponse({"status": 1, "msg": response_data['message']})
        else:
            messages.error(request, "PING QUERY GENERATION FAILED")
            return JsonResponse({"status": 0})

    # CASE 2: Regular query with zone
    elif query_type == "regular" and zone:
        # Step 1
        fixed_data = {
            "cmd_value": "ping",
            "cmd_type": "regular",
            "host_id": domain,
            "interval_time": "10",
            "interval_unit": "second",
            "query_status": "running",
            "anchor_id": [],
            "time_unit": "minute",
            "run_time": "1",
            "run_count": "3",
            "service_ids": [domain],
            "type_fo_query": "domain_zone_regular",
            "zone_id": [int(zone)]
        }
        print("Step 1 regular-zone payload........", fixed_data)
        response = requests.post(api_prefix_viz + "/api/anchor/preiodic-command-history-with-anchor-or-zone/",
                                 headers=header, json=fixed_data)
        response_data = response.json()
        print("Step 1 success regular-zone........", response_data)

        if response_data["status"] == 1:
            data_list = response_data["serialize_obj"]
            zone_anchor_user_ids = [item["user_id"] for item in data_list]

            # Step 2
            point_fix = {
                "anchor_user_id": 0,
                "anchor_user_ids": zone_anchor_user_ids,
                "command_name": "ping",
                "run_time": "1",
                "utilize_point": 5
            }
            print("Step 2 regular zone payload........", point_fix)
            response_point = requests.post(api_prefix_viz + "/api/subscription/point-utilization/", headers=header,
                                           json=point_fix)
            response_point_data = response_point.json()
            print("Step 2 regular zone ........", response_point_data)
            if response_point.status_code == 200:
                # Step 3: Call lease API
                for item in data_list:
                    chield_id = item.get("chield_id")
                    parent_id = item.get("parent_id")
                    lease_id = item.get("lease_id")
                    region = item.get("region")
                    anchors = item.get("anchors")

                    lease_api_payload = {
                        "region": region,
                        "anchors": anchors,
                        "cmd_type": "regular",
                        "cmd_value": "ping",
                        "hosts": [domain],
                        "run_count": "3",
                        "run_time": "1"
                    }
                    print("lease api payload....", lease_api_payload)
                    response_lease = requests.post(
                        api_prefix_rd3 + f"/apisrv/api/v1/ping/?lease_id={lease_id}",
                        headers={'Apikey': key_api},
                        json=lease_api_payload
                    )
                    lease_response_data = response_lease.json()
                    print(f"Lease API call response for Step 3: {lease_response_data.get('id')}")

                    if response_lease.status_code == 200:
                        dataset_list.append({
                            "chield_id": chield_id,
                            "parent_id": parent_id,
                            "query_id": lease_response_data.get('id'),
                            "status": "running"
                        })

                # Step 4
                gp_command_fixed_data = {"update_set": dataset_list}
                print("Step 4 payload......", gp_command_fixed_data)
                response_group_command = requests.put(api_prefix_viz + "/api/anchor/group-command-history/",
                                                      headers=header, json=gp_command_fixed_data)
                response_gp_data = response_group_command.json()
                if response_group_command.status_code == 200:
                    print("Step 4 successful group_command......", response_gp_data)

            return JsonResponse({"status": 1, "msg": response_data['message']})

        else:
            print("Step 1 failed for regular zone")
            return JsonResponse({"status": 0})

    # CASE 3: Periodic query with zone
    elif query_type == "periodic" and zone:
        fixed_data = {
            "cmd_value": "ping",
            "cmd_type": "periodic",
            "host_id": domain,
            "interval_time": int(interval_time),
            "interval_unit": interval_unit,
            "query_status": "enqueue",
            "anchor_id": [],
            "time_unit": time_unit,
            "run_time": int(time),
            "run_count": "3",
            "service_ids": [domain],
            "type_fo_query": "domain_zone_periodic",
            "zone_id": [int(zone)]
        }
        # print("Step 1 Periodic Zone payload........", fixed_data)
        response = requests.post(api_prefix_viz + "/api/anchor/preiodic-command-history-with-anchor-or-zone/",
                                 headers=header, json=fixed_data)
        response_data = response.json()
        # print("Step 1 Periodic Zone response........", response_data)

        if response_data["status"] == 1:
            data_list = response_data["serialize_obj"]
            zone_user_ids = [item["user_id"] for item in data_list]

            point_fix = {
                "anchor_user_id": 0,
                "anchor_user_ids": zone_user_ids,
                "command_name": "ping",
                "run_time": int(time),
                "utilize_point": 5
            }
            # print("Step 2  periodic zone payload.....", point_fix)
            response_point = requests.post(api_prefix_viz + "/api/subscription/point-utilization/", headers=header,
                                           json=point_fix)
            response_point_data = response_point.json()
            if response_point.status_code == 200:
                # print("Step 2 done successfully for periodic zone", response_point_data)
                return JsonResponse({"status": 1, "msg": response_point_data['message']})
            else:
                print("Error in Step 2 for Periodic Zone Time Query")
        else:
            print("Error in Step 1 Periodic Zone")
        return JsonResponse({"status": 0})

    # CASE 4: Regular query without zone (anchor-based)
    elif query_type == "regular" and not zone:
        point_fix = {
            "anchor_user_id": int(user_id),
            "anchor_user_ids": [],
            "command_name": "ping",
            "run_time": "1",
            "utilize_point": 5
        }
        print("Step 1 Payload...", point_fix)
        response_point = requests.post(api_prefix_viz + "/api/subscription/point-utilization/", headers=header,
                                       json=point_fix)
        response_point_data = response_point.json()
        print("Step 1 response...", response_point_data)
        if response_point.status_code == 200:
            fixed_data = {
                "cmd_value": "ping",
                "cmd_type": query_type,
                "hosts": domain,
                "anchor_ids": int(anchor_id),
                "region": anchor_location,
                "run_time": "1",
                "run_count": "3",
            }
            print("Step 2 payload...", fixed_data)
            response = requests.post(api_prefix_viz + "/api/anchor/command-history/", headers=header, json=fixed_data)
            response_data = response.json()
            print("Step 2 response...", response_data)
            command_id = response_data['obj_id']

            lease_data = {
                "cmd_value": "ping",
                "cmd_type": query_type,
                "hosts": [domain],
                "anchors": [anchor_anchor_id],
                "region": anchor_location,
                "run_count": "3"
            }
            print("Step 3 payload...", lease_data)
            response_lease = requests.post(
                api_prefix_rd3 + f"/apisrv/api/v1/ping/?lease_id={anchor_lease_id}",
                headers={'Apikey': key_api},
                json=lease_data
            )
            lease_response_data = response_lease.json()
            print("Step 3 response...", lease_response_data)
            query_id = lease_response_data["id"]

            gp_command_fixed_data = {
                "id": command_id,
                "query_id": query_id,
                "status": "running"
            }
            print("Step 4 payload...", gp_command_fixed_data)
            response_group_command = requests.put(api_prefix_viz + "/api/anchor/command-history/", headers=header,
                                                  json=gp_command_fixed_data)
            response_gp_data = response_group_command.json()
            print("Step 4 response...", response_gp_data)
            return JsonResponse({"status": 1, "msg": response_gp_data['message']})

    # Default fallback
    messages.error(request, "PING QUERY GENERATION FAILED")
    return JsonResponse({"status": 0})


@token_required
def ping_visualizer(request):
    id = request.GET.get("id")
    zone = request.GET.get("zone")
    query = request.GET.get("query")
    user_id = request.GET.get("user_id")
    # print(id, zone, query)

    token = request.token
    headers = {"Authorization": f"Bearer {token}"}
    user_data = request.session.get("profile_detail")
    if user_id:
        is_editable = int(user_id) == int(user_data.get("userid", ""))
    else:
        is_editable = True

    zone_queries = ZoneServices(token)
    zone_data = zone_queries.get_zone_data()
    assignment_service = AssignmentServices(token)
    assignment_response = assignment_service.get_assignment_data_by_students()
    assignment_data = assignment_response.get('assignments', "User Type is not student")

    command_fixed_data = {
        "id": int(id),
        "is_view": True
    }
    response_command = requests.put(api_prefix_viz + "/api/anchor/command-history/", headers=headers,
                                    json=command_fixed_data)
    response = response_command.json()
    # print(".........ping", response)
    if query == "regular":
        if response_command.status_code == 200 and zone in ["None", "", "null"]:

            command_payload = {
                "id": int(id)
            }
            print("Step 3 payload...", command_payload)
            result = requests.post(api_prefix_viz + "/api/anchor/command-result/",
                                   headers=headers, data=command_payload, )
            response_result = result.json()
            print(".........regular ping response", response_result)
            if response_result['data'] != []:

                anchor_data = {
                    "address": response_result['data'][0]['address'],
                    "rtt_min": response_result['data'][0]['rtt_min'],
                    "rtt_avg": response_result['data'][0]['rtt_avg'],
                    "rtt_max": response_result['data'][0]['rtt_max']
                }
                return render(request, 'services_app/ping_visualizer.html',
                              {"type": 1, "ping_data": response_result, 'json_data': json.dumps(response_result),
                               "history_id": id, 'anchor_data': json.dumps(anchor_data),
                               "user_data": user_data,
                               "assignment_list": assignment_data, "zone_list": zone_data.get('zone', ""),
                               "is_editable": is_editable})
            else:
                print(response_result['message'])

                return render(request, 'services_app/ping_visualizer.html',
                              {"type": 1, "ping_data": "", 'json_data': "",
                               "history_id": id, 'anchor_data': "",
                               "user_data": user_data,
                               "assignment_list": assignment_data, "zone_list": zone_data.get('zone', ""),
                               "is_editable": is_editable})



        elif response_command.status_code == 200 and zone != "None":

            command_payload = {
                "id": id
            }
            # print("Step 3 payload...", command)
            result = requests.post(api_prefix_viz + "/api/anchor/regular-zone-command-result/",
                                   headers=headers, json=command_payload)
            response_result = result.json()
            return render(request, 'services_app/ping_visualizer.html',
                          {"type": 2, "ping_data": response_result, 'json_data': json.dumps(response_result),
                           "history_id": id, 'data': json.dumps(response_result['data']),
                           "user_data": user_data, "assignment_list": assignment_data,
                           "zone_list": zone_data.get('zone', ""), "is_editable": is_editable})

    elif query == "periodic":
        if zone != "":
            command_payload = {
                "id": int(id)
            }
            # print("Step 1 command payload....", command_payload)
            result = requests.post(api_prefix_viz + "/api/anchor/periodic-result-by-id/",
                                   headers=headers, json=command_payload)
            response_result = result.json()
            print("Step 1 command request....", response_result)
            if result.status_code == 200:
                payload = {
                    "history_id": int(id),
                    "user_id": user_id
                }
                # print("Step 2 payload....", payload)
                command_request = requests.post(api_prefix_viz + "/api/anchor/command-history-details/",
                                                headers=headers, json=payload)
                command_result = command_request.json()
                # print("Step 2 command result....", command_result)
                if command_request.status_code == 200:
                    duartion = command_result['history']['query_execution_interval_time']
                    from_date = command_result['history']['created_date']
                    to_date = command_result['history']['query_execution_end_date']
                    periodic_payload = {
                        "id": int(id),
                        "duration": duartion,
                        "from_date": from_date,
                        "to_date": to_date
                    }
                    # print("Step 3 payload....", periodic_payload)
                    periodic_result = requests.post(api_prefix_viz + "/api/anchor/zone-periodic-result/",
                                                    headers=headers, json=periodic_payload)
                    response_periodic = periodic_result.json()
                    print("Step 3 result....", response_periodic)

                    return render(request, 'services_app/ping_visualizer.html',
                                  {"type": 4, "ping_data": command_result['history'],
                                   'json_data': json.dumps(response_result), "rtt_datas": response_result['data'],
                                   "history_id": id, "user_data": user_data,
                                   "assignment_list": assignment_data, "zone_list": zone_data.get('zone', ""),
                                   "is_editable": is_editable})

        elif zone == "":
            command_fixed_data = {
                "id": int(id),
                "is_view": True
            }

            # print("Step 1 payload....", command_fixed_data)
            response_command = requests.put(api_prefix_viz + "/api/anchor/command-history/", headers=headers,
                                            json=command_fixed_data)
            response = response_command.json()
            # print("Step 1 response....", response)
            if response_command.status_code == 200:

                command_payload = {
                    "id": int(id)
                }
                # print("Step 2 command payload....", command_payload)
                result = requests.post(api_prefix_viz + "/api/anchor/periodic-result-by-id/",
                                       headers=headers, json=command_payload)
                response_result = result.json()
                # print("Step 2 command request....", response_result)
                if result.status_code == 200:
                    payload = {
                        "history_id": int(id),
                        "user_id": user_id
                    }
                    # print("Step 3 payload....", payload)
                    command_request = requests.post(api_prefix_viz + "/api/anchor/command-history-details/",
                                                    headers=headers, json=payload)
                    command_result = command_request.json()
                    # print("Step 3 command result....", command_result)
                    if command_request.status_code == 200:
                        duartion = command_result['history']['query_execution_interval_time']
                        from_date = command_result['history']['created_date']
                        to_date = command_result['history']['query_execution_end_date']
                        periodic_payload = {
                            "id": int(id),
                            "duration": duartion,
                            "from_date": from_date,
                            "to_date": to_date
                        }
                        # print("Step 4 payload....", periodic_payload)
                        periodic_result = requests.post(api_prefix_viz + "/api/anchor/periodic-result/",
                                                        headers=headers, json=periodic_payload)
                        response_periodic = periodic_result.json()
                        # print("Step 4 reult....", response_periodic)

                        return render(request, 'services_app/ping_visualizer.html',
                                      {"type": 3, "ping_data": command_result['history'],
                                       'json_data': json.dumps(response_periodic),
                                       "history_id": id, "user_data": user_data,
                                       "assignment_list": assignment_data, "zone_list": zone_data.get('zone', ""),
                                       "is_editable": is_editable})


@token_required
def enroll_students(request):
    """Fetch students enrolled by faculty."""
    token = request.token
    student_service = StudentServices(token)
    response_data = student_service.get_enroll_students()
    user_data = request.session.get("profile_detail")
    ip = request.session.get('ip_address')
    return render(request, 'services_app/enroll_students.html',
                  {"student_list": response_data[1], "user_data": user_data,
                   'ip': ip})


@token_required
def create_student(request):
    """Adds student by faculty."""
    token = request.token
    student_service = StudentServices(token)
    password = request.POST.get("password")
    email = request.POST.get("email")
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    mobile = request.POST.get("mobile")
    institution_name = request.POST.get("institute")
    student_id = request.POST.get("student_id")
    status_code, response_data = student_service.add_student(password=password, email=email, first_name=first_name,
                                                             last_name=last_name, mobile=mobile, student_id=student_id,
                                                             institution_name=institution_name)

    if status_code == 201:

        return JsonResponse({"status": 1, "msg": response_data.get('message', 'Student created successfully.')})
    else:
        print("=======", response_data)
        messages.error(request, response_data.get('message', 'Student Creation FAILED'))
        return JsonResponse({"status": 0, "msg": response_data.get('message', 'Student Creation FAILED')})


@token_required
def delete_student(request):
    """Deletes a student by email by faculty."""
    token = request.token
    student_service = StudentServices(token)
    email = request.POST.get("email")
    status_code, result = student_service.delete_student(email)
    if status_code == 204:
        return JsonResponse({"status": 1})
    else:
        messages.error(request, result.get("message", "Student removal FAILED"))
        return JsonResponse({"status": 0, "msg": result.get("message", "Student removal FAILED")})


@token_required
def student_details_fetch_by_mail(request):
    """Fetch points assigned to student by Faculty during student creation."""
    token = request.token
    email = request.POST.get("email")
    points_service = SubsciptionServices(token)
    response_data = points_service.get_point_assigned_to_student(email=email)
    points = get_remaining_points_by_user(response_data['user_id'])
    response_data['points'] = points
    return JsonResponse({"status": 1, "data": response_data})


@token_required
def student_point_details_fetch_by_userid(request):
    """Fetch point utilization data of student by Faculty."""
    token = request.token
    user_id = request.POST.get("user_id")
    points_service = SubsciptionServices(token)
    response_data = points_service.get_point_utilization_data_of_student(user_id=user_id)
    return JsonResponse({"status": 1, "point_details": response_data['utilization']})


@token_required
def recharge_points_students(request):
    """Recharge points to students by faculty."""
    token = request.token
    student_user_id = request.POST.get("student_user_id")
    recharge_points = request.POST.get("recharge_points")
    points_service = SubsciptionServices(token)
    response_data = points_service.recharge_points_to_students(student_user_id=student_user_id,
                                                               recharge_points=recharge_points)
    return JsonResponse({"status": 1, "data": response_data})


@method_decorator(token_required, name='dispatch')
class AssignmentView(View):
    def get(self, request, *args, **kwargs):
        token = request.token
        assignment_service = AssignmentServices(token)
        user_data = request.session.get("profile_detail")
        ip = request.session.get('ip_address')
        user_type = user_data["is_student"]
        if user_type is True:
            """Fetch all assignments created by faculty view from students window."""
            assignment_data = assignment_service.get_assignment_data_by_students()

        else:
            """Fetch all assignments created by faculty."""
            assignment_data = assignment_service.get_assignment_data()

        return render(request, 'services_app/assignments.html',
                      {"assignment_list": assignment_data.get('assignments', ""), "user_data": user_data,
                       'ip': ip})

    def post(self, request, *args, **kwargs):
        """Create assignments by faculty."""
        token = request.token
        action_type = request.POST.get("action_type")
        assigment_service = AssignmentServices(token)
        if action_type == "add_assignment":
            assignment_name = request.POST.get("assignment_name")
            uploaded_doc = request.FILES.get("assignmentfile")
            remarks = request.POST.get("assignment_remarks")
            assignment_post = assigment_service.add_assignment_data(assignment_name=assignment_name,
                                                                    uploaded_doc=uploaded_doc, remark=remarks)
            return JsonResponse(assignment_post)

        elif action_type == "update_assignment":
            status = request.POST.get("status")
            remark = request.POST.get("remark")
            assignment_id = request.POST.get("assignment_id")

            assignment_update = assigment_service.edit_assignment(assignment_id=assignment_id, status=status,
                                                                  remarks=remark)
            return JsonResponse(assignment_update)

        elif action_type == "delete_assignment":
            assignment_id = request.POST.get("assignment_id")
            assignment_delete = assigment_service.delete_assignment(assignment_id=assignment_id)
            return JsonResponse(assignment_delete)

        # fallback
        return JsonResponse({"status": 0, "message": "Invalid action type"})


@token_required
def query_linking_by_student(request):
    """Link queries to assignment by students"""
    token = request.token
    assignment = request.POST.get("assignment")
    command = request.POST.get("command")
    query_id = request.POST.get("query_id")
    assignment_query_type = request.POST.get("assignment_query_type")
    assignment_zone = request.POST.get("assignment_zone")
    assignment_remarks = request.POST.get("assignment_remarks")
    assignment_service = AssignmentServices(token)

    print("linking query....", assignment_zone, assignment_query_type)
    response_data = assignment_service.link_queries_to_assignment(assignment_name=assignment, command=command,
                                                                  query_id=query_id, remarks=assignment_remarks,
                                                                  query_type=assignment_query_type,
                                                                  zone=assignment_zone)
    return JsonResponse({"status": 1, "data": response_data})


@token_required
def editing_linkedquery_by_student(request):
    """Student can edit & delete Linked Queries"""
    token = request.token
    action_type = request.POST.get("action_type")
    assigment_service = AssignmentServices(token)
    if action_type == 'update_linked_query':
        query_id = request.POST.get('query_id')
        remark = request.POST.get('remark')
        query_update = assigment_service.edit_linked_queries_by_student(query_id=query_id, remarks=remark)
        return JsonResponse(query_update)

    elif action_type == 'delete_linked_query':
        linked_id = request.POST.get('linked_id')
        query_delete = assigment_service.delete_linked_queries_by_student(query_id=linked_id)
        return JsonResponse(query_delete)

    # fallback
    return JsonResponse({"status": 0, "message": "Invalid action type"})


@token_required
def associated_measurement_logs(request):
    """Fetch assignment wise linked queries by students results in faculty dashboard"""
    token = request.token
    assignment_id = request.GET.get("id")
    user_data = request.session.get("profile_detail")
    assignments_data = AssignmentServices(token)
    response_data = assignments_data.get_associated_measurement_logs(assignment_id=assignment_id)
    ip = request.session.get('ip_address')
    return render(request, 'services_app/associated_measurements.html',
                  {"user_data": user_data, "assignment_details": response_data,
                   'ip': ip})


@token_required
def student_linked_queries_by_userid(request):
    """To view from faculty's window linked queries by students"""
    token = request.token
    user_id = request.POST.get("user_id")
    linked_data = AssignmentServices(token)
    response_data = linked_data.get_studentwise_measurement_logs(user_id=user_id)
    return JsonResponse({"status": 1, "linked_queries": response_data["assignments"]})


@token_required
def linked_queries_by_student_dashboard(request):
    """To view from student's window linked queries by individual student"""
    token = request.token
    user_data = request.session.get("profile_detail")
    linked_data = AssignmentServices(token)
    response_data = linked_data.get_linked_queries_by_individual()
    ip = request.session.get('ip_address')
    return render(request, 'services_app/linked_queries.html',
                  {"user_data": user_data, "query_list": response_data,
                   'ip': ip})


# Admin code starts from here
@token_required
def user_list(request):
    token = request.token
    header = {'Authorization': f'Bearer {token}'}
    response = requests.get(api_prefix_viz + "/api/user/user-list/", headers=header)
    res_json = response.json()
    user_data = request.session.get("profile_detail")
    return render(request, 'services_app/user_list.html',
                  {"user_list": res_json.get("users", []), "user_data": user_data})


@token_required
def user_list_point_details(request):
    token = request.token
    header = {'Authorization': f'Bearer {token}'}
    response = requests.get(api_prefix_viz + "/api/subscription/user-point/", headers=header)
    res_json = response.json()
    user_data = request.session.get("profile_detail")
    return render(request, 'services_app/user_list_point_details.html',
                  {"user_list": res_json.get("data_list", []), "user_data": user_data})


@token_required
def user_report(request):
    token = request.token
    user_id = request.POST.get('user_id')
    report_type = request.POST.get('report_type')
    zone_service = ZoneServices(token)
    profile_service = ProfileServices(token)
    subscription_services = SubsciptionServices(token)
    if report_type == "user_zone_report":
        return JsonResponse(
            zone_service.get_zone_report_data(user_id=user_id)
        )
    elif report_type == "user_profile_report":
        return JsonResponse(
            profile_service.get_profile_report_data(user_id=user_id)
        )
    elif report_type == "user_point_utilization_report":
        return JsonResponse(
            subscription_services.get_point_spend_report_data(user_id=user_id)
        )
    elif report_type == "user_subscription_report":

        return JsonResponse(
            subscription_services.get_report_plan_data(user_id=user_id)
        )
    return JsonResponse({"status": 0, "message": "Invalid action type"})


@token_required
def point_addition_admin(request):
    token = request.token
    header = {'Authorization': f'Bearer {token}'}
    user_id = request.POST.get("user_id")
    points = request.POST.get("points")
    subscription_id = request.POST.get("subscription_id")
    payload = {
        "user_id": int(user_id),
        "points": int(points),
        # "subscription_id": int(subscription_id)
    }
    print("Payload for adding points:", payload)
    response = requests.post(api_prefix_viz + "/api/subscription/user-point/", headers=header, json=payload)
    try:
        res_json = response.json()
    except Exception as e:
        # For AJAX requests, always return a minimal JSON error, not a debug page
        return JsonResponse({"status": 0, "msg": "Failed to add points. Invalid response from server."})

    if res_json.get("status") == 1:
        return JsonResponse({"status": 1, "msg": "Points added successfully."})
    else:
        return JsonResponse({"status": 0, "msg": res_json.get("message", "Failed to add points.")})


@token_required
def admin_anchor_list(request):
    token = request.token
    header = {'Authorization': f'Bearer {token}'}
    response = requests.get(api_prefix_viz + "/api/anchor/anchor-request/", headers=header)
    res_json = response.json()
    user_data = request.session.get("profile_detail")
    return render(request, 'services_app/admin_anchor_list.html',
                  {"anchor_list": res_json.get("anchor", []), "user_data": user_data})


@token_required
def public_measurement(request):
    token = request.token
    user_data = request.session.get("profile_detail")
    ip = request.session.get('ip_address')
    return render(request, 'services_app/centralized_measurements.html', {"user_data": user_data, 'ip': ip})


@token_required
def public_report(request):
    token = request.token
    header = {'Authorization': f'Bearer {token}'}

    if request.method == "POST":
        report_id = request.POST.get("id")
        is_public = request.POST.get("is_public")

        if not report_id:
            return JsonResponse({"status": 0, "msg": "History ID is required."})

        if isinstance(is_public, str):
            is_public = is_public.lower() == "true"

        payload = {
            "id": int(report_id),
            "is_public": is_public
        }

        try:
            response = requests.patch(api_prefix_viz + "/api/anchor/command-history/", headers=header, data=payload)
            try:
                res_json = response.json()
            except ValueError:
                res_json = {}

            if response.status_code == 200:
                return JsonResponse({"status": 1, "msg": "Report visibility updated successfully."})
            else:
                error_msg = res_json.get("message", "Failed to update report visibility.")
                return JsonResponse({"status": 0, "msg": error_msg})

        except Exception as e:
            return JsonResponse({"status": 0, "msg": str(e)})

    return JsonResponse({"status": 0, "msg": "Invalid request method."})


def engagement_opportunity(request):
    return render(request, 'services_app/engagement_opportunity.html')


@token_required
def qr_code_list_view(request):
    token = request.token
    user_data = request.session.get("profile_detail")

    # Check if it's an AJAX request (JSON expected)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('as_json'):
        headers = {
            "Authorization": f"Bearer {token}"
        }
        try:
            url = api_prefix_viz + "/api/anchor/qr-codes/"
            params = {
                "start_date": request.GET.get("start_date"),
                "end_date": request.GET.get("end_date")
            }
            params = {k: v for k, v in params.items() if v}
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                qr_codes = data.get("qr_files", [])
            else:
                qr_codes = []
        except Exception as e:
            print(f"QR Fetch Error: {e}")
            qr_codes = []

        return JsonResponse({"qr_files": qr_codes})

    # If not AJAX, render full HTML
    return render(request, 'services_app/admin_qr_code_list.html', {
        "user_data": user_data
    })


@token_required
def admin_faculty_student_list(request):
    token = request.token
    header = {'Authorization': f'Bearer {token}'}
    response = requests.get(api_prefix_viz + "/api/user/user-stats/?is_faculty=true", headers=header)
    res_json = response.json()
    user_data = request.session.get("profile_detail")
    return render(request, 'services_app/admin_faculty_students_dashboard.html',
                  {"faculty_list": res_json.get("faculty_users", []), "user_data": user_data,
                   "total_faculties": res_json.get("total_faculties", ""),
                   "total_students": res_json.get("total_students", "")})


@token_required
def faculty_student_list(request):
    token = request.token
    user_id = request.POST.get('user_id')
    header = {'Authorization': f'Bearer {token}'}
    response = requests.get(api_prefix_viz + "/api/user/faculty-students/?faculty_id=" + user_id)
    res_json = response.json()
    # print("Faculty and student details fetched successfully", res_json)
    if res_json.get("status") == 1:
        return JsonResponse(
            {"status": 1, "data": res_json.get("data", []), "message": res_json.get("message", "")})  # Success response
    else:
        return JsonResponse({"status": 0, "message": "Invalid action type"})

def custom_404_view(request, exception):
    return render(request, 'services_app/auth-404.html', status=404)

def custom_500_view(request):
    return render(request, 'services_app/auth-500.html', status=500)


@token_required
def export_user_report(request):

    token = request.token

    header = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(
        api_prefix_viz + "/api/subscription/export-user-report/",
        headers=header
    )

    if response.status_code != 200:
        return HttpResponse("Failed to fetch report", status=400)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = now().astimezone(ist).strftime("%d-%m-%Y_%-I:%M%p")
    current_time = current_time.replace("AM", "_AM").replace("PM", "_PM")
    filename = f"user_report_{current_time}.csv"

    django_response = HttpResponse(
        response.content,
        content_type='text/csv'
    )
    django_response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return django_response