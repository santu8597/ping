from django.shortcuts import render

# Create your views here.
import json
from django.views import View
from django.http import JsonResponse
from backend.users.models import CustomUser
from django.contrib.auth.hashers import make_password, check_password
from services.email_service import EmailHelper
from backend.utils.helpers import send_otp, get_cache, delete_cache
from services.twilio.twilio import TwilioVerifyService


class SendOTPView(View):
    def post(self, request, *args, **kwargs):
        """
        Generates and sends OTP to the provided email address.
        """
        # Parse the JSON request body
        data = json.loads(request.body.decode('utf-8'))

        # Get the email from the parsed data
        email = data.get('email')
        # Check if email is provided
        if not email:
            return JsonResponse({"error": "Email is required."}, status=400)

        if CustomUser.objects.filter(email=email).exists():
            return JsonResponse({"status": "error", "message": "Email already registered."}, status=400)

        try:
            otp_response = send_otp(email)

            if otp_response["status"] == "success":
                return JsonResponse({"status": "success", "message": "OTP sent successfully!"})
            else:
                return JsonResponse({"status": "error", "message": otp_response["message"]}, status=400)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class ValidateOTPView(View):
    def post(self, request, *args, **kwargs):
        """
        Handles OTP validation.
        """
        try:
            data = json.loads(request.body)
            email = data.get('email')
            otp = data.get('otp')
        except KeyError:
            return JsonResponse({"status": "error", "message": "Missing parameters."}, status=400)

        if not email or not otp:
            return JsonResponse({"status": "error", "message": "Email and OTP are required."}, status=400)

        # Retrieve the stored OTP from the cache
        stored_otp = get_cache('otp_cache', email)

        if not stored_otp:
            return JsonResponse({"status": "error", "message": "OTP has expired or is invalid."}, status=400)

        # Check if the OTP is valid by comparing with the stored hash
        if not check_password(otp, stored_otp):
            return JsonResponse({"status": "error", "message": "Invalid OTP. Please try again."}, status=400)

        # OTP is valid, remove it from cache and proceed
        delete_cache('otp_cache', email)  # Clean up after successful validation

        return JsonResponse({"status": "success", "message": "OTP validated successfully!"}, status=200)


class SendMobileOTPView(View):
    def post(self, request, *args, **kwargs):
        """
        Sends an OTP to the provided mobile number using Twilio Verify.
        """
        try:
            data = json.loads(request.body.decode('utf-8'))
            mobile = data.get('mobile')
            print("OTP.......................", mobile)

            if not mobile:
                return JsonResponse({"error": "Mobile number is required."}, status=400)

            if CustomUser.objects.filter(phone_no=mobile).exists():
                return JsonResponse({"status": "error", "message": "Mobile number already registered."}, status=400)

            twilio = TwilioVerifyService()
            otp_response = twilio.send_otp_to_mobile(f"+91{mobile}")
            print("otp response............", otp_response)

            if otp_response.get("success"):
                return JsonResponse({"status": "success", "message": "OTP sent successfully!"})
            else:
                return JsonResponse({"status": "error", "message": otp_response.get("message", "Failed to send OTP.")},
                                    status=400)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class VerifyMobileOTPView(View):
    def post(self, request, *args, **kwargs):
        """
        Verifies the OTP entered by the user for the given mobile number.
        """
        try:
            data = json.loads(request.body.decode('utf-8'))
            mobile = data.get('mobile')
            otp = data.get('otp')

            if not mobile or not otp:
                return JsonResponse({"error": "Mobile number and OTP are required."}, status=400)

            twilio = TwilioVerifyService()
            verification_result = twilio.verify_otp(f"+91{mobile}", otp)

            if verification_result.get("status") == "approved":
                return JsonResponse({"status": "success", "message": "OTP verified successfully!"})
            else:
                return JsonResponse({"status": "error", "message": "Invalid or expired OTP."}, status=400)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class ResendOTP(View):
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        try:
            if not email:
                return JsonResponse({"status": "error", "message": "Missing required parameters"}, status=400)

            otp_response = send_otp(email)

            if otp_response["status"] == "success":
                return JsonResponse({"status": "success", "message": "OTP sent successfully!"}, status=200)
            else:
                return JsonResponse({"status": "error", "message": otp_response["message"]}, status=400)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
