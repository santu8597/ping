from twilio.rest import Client
import os

from config_env import CONFIG


class TwilioVerifyService:
    def __init__(self, account_sid=None, auth_token=None, service_sid=None):
        self.account_sid = account_sid or CONFIG.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or CONFIG.TWILIO_AUTH_TOKEN
        self.service_sid = service_sid or CONFIG.TWILIO_VERIFY_SERVICE_SID
        self.client = Client(self.account_sid, self.auth_token)

    def send_otp_to_mobile(self, phone):
        """
        Sends an OTP to the given phone number using Twilio Verify.
        """
        try:
            verification = self.client.verify \
                .v2 \
                .services(self.service_sid) \
                .verifications \
                .create(to=phone, channel="sms")
            return {"status": verification.status, "success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_otp(self, phone, code):
        """
        Verifies the OTP entered by the user.
        """
        try:
            verification_check = self.client.verify \
                .v2 \
                .services(self.service_sid) \
                .verification_checks \
                .create(to=phone, code=code)
            return {
                "status": verification_check.status,
                "success": verification_check.status == "approved"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
