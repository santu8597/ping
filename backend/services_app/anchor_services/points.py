import os
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

load_dotenv()
# Create your views here.
api_prefix_viz = os.getenv('API_URL_VIZ')
api_prefix_rd3 = os.getenv('API_URL_RD3')


class SubsciptionServices:
    def __init__(self, token):
        """
        Initialize with the Bearer token for authorization.
        """
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}

        # For safe removal of external subscription dependency we keep a local stub.
        # If you want to re-enable real subscription calls, set `API_URL_VIZ`
        # and restore the original implementation.
        self.api_prefix_viz = api_prefix_viz or None

    def make_request(self, method, endpoint, data=None):
        # Stubbed network calls: return a safe default instead of performing
        # external HTTP requests. This makes removing the subscription
        # backend safe while keeping existing call sites functioning.
        return {"status": 0, "message": "Subscription backend disabled (stub)."}

    def get_subscription_data(self):
        """
        Fetch domain data from the external API using the API_PREFIX_VIZ from environment.
        Returns the response data if successful, otherwise raises an exception.
        """
        # Return a minimal, safe subscription structure used by templates
        return {
            "status": 1,
            "plans": [
                {
                    "package": {"package_name": "None", "package_description": "Subscription removed"},
                }
            ],
            "total_points": 0,
            "used_points": 0,
            "remaining_points": 0,
            "package_activation_date": None,
            "package_deactivation_date": None,
        }

    def get_point_utilization_data(self):
        """
        Fetch point utilization data of  user.
        Returns the response data if successful, otherwise raises an exception.
        """
        return {"status": 1, "points": []}

    def recharge_points_to_students(self, student_user_id, recharge_points):
        """
        Recharge points to students by faculty.
        Returns a response indicating success or failure.
        """
        # No-op stub: pretend recharge succeeded when subscription system is disabled.
        return {"status": 1}

    def get_point_utilization_data_of_student(self, user_id):
        """
        Fetch point utilization data of  student by Faculty.
        Returns the response data if successful, otherwise raises an exception.
        """
        return {"status": 1, "points": []}

    def get_point_assigned_to_student(self, email):
        """
        Fetch points assigned to student by Faculty during student creation.
        Returns the response data if successful, otherwise raises an exception.
        """
        return {"status": 1, "points": []}
    def get_point_spend_report_data(self, user_id):
        """
        Fetch user profile data from the external API using the API_PREFIX_VIZ from environment.
        Returns the response data if successful, otherwise raises an exception.
        """
        return {"status": 1, "points": []}
    def get_report_plan_data(self, user_id):
        """
        Fetch user profile data from the external API using the API_PREFIX_VIZ from environment.
        Returns the response data if successful, otherwise raises an exception.
        """
        return {"status": 1, "subscriptions": []}