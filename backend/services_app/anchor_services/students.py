import os
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

load_dotenv()
# Create your views here.
api_prefix_viz = os.getenv('API_URL_VIZ')
api_prefix_rd3 = os.getenv('API_URL_RD3')


class StudentServices:
    def __init__(self, token):
        """
        Initialize with the Bearer token for authorization.
        """
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}

        self.api_prefix_viz = api_prefix_viz

        if not self.api_prefix_viz:
            raise ValueError("API_PREFIX_VIZ environment variable is not set.")

    def make_request(self, method, endpoint, data=None):
        """
        Helper function to make GET or POST requests with error handling.

        Returns a tuple: (status_code, response_json)
        """
        url = f"{self.api_prefix_viz}{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            return response.status_code, response.json()

        except RequestException as e:
            return 500, {"message": f"An error occurred: {str(e)}"}

    def get_enroll_students(self):
        """
        Fetch students enrolled by faculty.
        Returns the response data if successful, otherwise raises an exception.
        """
        endpoint = "/api/user/faculty/students/"
        return self.make_request('GET', endpoint)

    def add_student(self, password, email, first_name, last_name, mobile, student_id, institution_name):
        """
        Adds student by faculty.
        Returns a response indicating success or failure.
        """
        payload = {
            "password": password,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone_no": mobile,
            "student_id": student_id,
            "institution_name": institution_name,
        }
        endpoint = "/api/user/student/create/"
        status_code, response_json = self.make_request('POST', endpoint, payload)

        return status_code, response_json

    def delete_student(self, email):
        """
        Deletes a student by email by faculty.
        Returns a tuple: (status_code, response_json_or_message)
        """
        endpoint = f"/api/user/student/profile/?email={email}"
        try:
            response = requests.delete(f"{self.api_prefix_viz}{endpoint}", headers=self.headers)

            if response.status_code == 204:
                return 204, {"message": "Student deleted successfully."}
            else:
                return response.status_code, response.json()
        except RequestException as e:
            return 500, {"message": f"An error occurred: {str(e)}"}
