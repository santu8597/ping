import os
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

load_dotenv()
# Create your views here.
api_prefix_viz = os.getenv('API_URL_VIZ')
api_prefix_rd3 = os.getenv('API_URL_RD3')


class AssignmentServices:
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

        - `method`: HTTP method ('GET' or 'POST')
        - `endpoint`: API endpoint
        - `data`: data to send (only for POST requests)
        """
        url = f"{self.api_prefix_viz}{endpoint}"

        try:
            # Send the request based on the method
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check if the request was successful
            response.raise_for_status()

            # Return the JSON data if response is successful
            return response.json()

        except RequestException as e:
            # Handle any request errors (timeout, network issues, etc.)
            return {"status": 0, "message": f"An error occurred: {str(e)}"}

    def make_request_with_files(self, method, endpoint, data=None):
        """
        Helper function to make GET or POST requests with error handling.
        Dynamically detects files and sends them using the correct format.
        """
        url = f"{self.api_prefix_viz}{endpoint}"

        form_data = {}
        file_data = {}

        if data:
            for key, value in data.items():
                if hasattr(value, 'read'):  # It's a file-like object
                    file_data[key] = (value.name, value, value.content_type if hasattr(value,
                                                                                       'content_type') else 'application/octet-stream')
                else:
                    form_data[key] = value

        # Make a copy of headers to avoid modifying the original
        headers = self.headers.copy()

        # If files are present, remove Content-Type so requests can set it
        if file_data and 'Content-Type' in headers:
            headers.pop('Content-Type')

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                if file_data:
                    response = requests.post(url, headers=headers, data=form_data, files=file_data)
                else:
                    response = requests.post(url, headers=headers, json=form_data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except RequestException as e:
            return {"status": 0, "message": f"An error occurred: {str(e)}"}

    def add_assignment_data(self, assignment_name, uploaded_doc, remark):
        """
        Create assignments by faculty.
        Returns a response indicating success or failure.
        """
        assignment_fix = {
            "assignment_name": assignment_name,
            "uploaded_doc": uploaded_doc,
            "remark": remark,
            "status": "ongoing"
        }
        endpoint = "/api/user/faculty/assignments/"
        response = self.make_request_with_files('POST', endpoint, assignment_fix)
        if response['status'] == 1:
            return {"status": 1}  # Success response
        else:
            return {"status": 0, "message": response.get("message", "ASSIGNMENT ADDITION FAILED")}

    def get_assignment_data(self):
        """
        Fetch all assignments created by faculty.
        Returns the response data if successful, otherwise raises an exception.
        """
        endpoint = "/api/user/faculty/assignments/"
        return self.make_request('GET', endpoint)

    def get_assignment_data_by_students(self):
        """
        Fetch all assignments created by faculty in student's window.
        Returns the response data if successful, otherwise raises an exception.
        """
        endpoint = "/api/user/student/view/assignments/"
        return self.make_request('GET', endpoint)

    def link_queries_to_assignment(self, assignment_name, command, query_id, remarks, query_type, zone):
        """
        Link queries to assignment by students
        Returns a response indicating success or failure.
        """
        # needs modification later
        if query_type == "regular":
            zone = zone if zone else "None"
            link_queries = {
                "assignment": assignment_name,
                "remark": remarks,
                "command": command,
                "query_id": query_id,
                "zone": zone,
                "query_type": query_type
            }
        else:
            link_queries = {
                "assignment": assignment_name,
                "remark": remarks,
                "command": command,
                "query_id": query_id,
                "zone": zone,
                "query_type": query_type
            }

        endpoint = "/api/user/student/assignments/"
        response = self.make_request('POST', endpoint, link_queries)

        if response.get("status") == 1:
            return {"status": 1}  # Success response
        else:
            return {"status": 0, "message": response.get("message", "Query Linking Failed")}

    def edit_linked_queries_by_student(self, query_id, remarks):
        """For students can edit remarks for linked query"""
        payload = {
            "remark": remarks
        }
        endpoint = "/api/user/student/assignments/" + query_id + "/"
        update_request = requests.patch(api_prefix_viz + endpoint, payload, headers=self.headers)
        response = update_request.json()

        if update_request.status_code == 200:
            return {"status": 1, "response": response}
        else:
            return {"status": 0, "response": response}

    def delete_linked_queries_by_student(self, query_id):
        """Sends a DELETE request to  delete the linked queries by student."""

        endpoint = "/api/user/student/assignments/" + query_id + "/"
        delete_request = requests.delete(api_prefix_viz + endpoint, headers=self.headers)
        response = delete_request.json()

        if delete_request.status_code == 200:
            return {"status": 1, "response": response}
        else:
            return {"status": 0, "response": response}

    def get_associated_measurement_logs(self, assignment_id):
        """
        Fetch assignment wise linked queries by students results in faculty dashboard
        Returns the response data if successful, otherwise raises an exception.
        """
        endpoint = "/api/user/assignments/" + assignment_id + "/linked-queries/"
        return self.make_request('GET', endpoint)

    def get_studentwise_measurement_logs(self, user_id):
        """
        To view from faculty's window linked queries by students
        Returns the response data if successful, otherwise raises an exception.
        """
        endpoint = "/api/user/faculty/student/" + user_id + "/assignments/"
        return self.make_request('GET', endpoint)

    def get_linked_queries_by_individual(self):
        """
        To view from student's window linked queries by individual student
        Returns the response data if successful, otherwise raises an exception.
        """
        endpoint = "/api/user/student/assignments/"
        return self.make_request('GET', endpoint)

    def delete_assignment(self, assignment_id):
        """
        Sends a DELETE request to mark the delete the assignments.
        """

        endpoint = "/api/user/faculty/assignments/" + assignment_id + "/"
        delete_request = requests.delete(api_prefix_viz + endpoint, headers=self.headers)
        response = delete_request.json()
        if delete_request.status_code == 200:
            return {"status": 1, "response": response}
        else:
            return {"status": 0, "response": response}

    def edit_assignment(self, assignment_id, status, remarks):

        payload = {
            "status": status,
            "remark": remarks
        }

        endpoint = "/api/user/faculty/assignments/" + assignment_id + "/"
        update_request = requests.patch(api_prefix_viz + endpoint, payload, headers=self.headers)
        response = update_request.json()

        if update_request.status_code == 200:
            return {"status": 1, "response": response}
        else:
            return {"status": 0, "response": response}
