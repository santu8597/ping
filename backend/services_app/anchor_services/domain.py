import os
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv
from datetime import datetime, timezone
from dateutil.parser import isoparse

load_dotenv()
# Create your views here.
api_prefix_viz = os.getenv('API_URL_VIZ')
api_prefix_rd3 = os.getenv('API_URL_RD3')


class DomainServices:
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
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check if the request was successful
            response.raise_for_status()

            # Return the JSON data if response is successful
            return response.json()

        except RequestException as e:
            # Handle any request errors (timeout, network issues, etc.)
            return {"status": 0, "message": f"An error occurred: {str(e)}"}

    def get_time(self, domain_response):
        modified_times = [
            isoparse(domain['modified_date'])
            for domain in domain_response.get('domain', [])
            if 'modified_date' in domain
        ]

        if not modified_times:
            return None, None, "No domains found"

        latest_time = max(modified_times)
        current_time = datetime.now(timezone.utc)
        time_diff = current_time - latest_time

        if time_diff.days > 0:
            diff_str = f"{time_diff.days} days ago"
        elif time_diff.seconds >= 3600:
            hours = time_diff.seconds // 3600
            diff_str = f"{hours} hours ago"
        elif time_diff.seconds >= 60:
            minutes = time_diff.seconds // 60
            diff_str = f"{minutes} minutes ago"
        else:
            diff_str = "Just now"

        return latest_time.isoformat(), current_time.isoformat(), diff_str

    def get_domain_data(self):
        """
        Fetch domain data from the external API using the API_PREFIX_VIZ from environment.
        Returns the response data if successful, otherwise raises an exception.
        """
        endpoint = "/api/user/user-domain/"
        response = self.make_request('GET', endpoint)
        # print(response)
        latest_time, current_time, diff_str = self.get_time(response)

        # Send to frontend
        return {
            "domain": response.get("domain", []),
            "latest_time": latest_time,
            "current_time": current_time,
            "time_diff": diff_str
        }

    def add_domain_data(self, domain_name, domain_ip):
        """
        Adds domain data to the external API.
        Returns a response indicating success or failure.
        """
        domain_fix = {
            "domain_name": domain_name,
            "ip": domain_ip
        }
        endpoint = "/api/user/user-domain/"
        response = self.make_request('POST', endpoint, domain_fix)

        if response.get("status") == 1:
            return {"status": 1, "obj_id": response.get("obj_id")}  # Success response
        else:
            return {"status": 0, "message": response.get("message", "DOMAIN ADDITION FAILED")}

    def delete_domain_data(self, domain_id):
        """
        Sends a PUT request to mark the domain as deleted by setting is_delete=True.
        """
        # Construct payload
        payload = {
            "domain_id": domain_id,
            "is_delete": True
        }

        # Define the endpoint
        endpoint = "/api/user/user-domain/"

        # Make the PUT request using the helper function
        response = self.make_request('PUT', endpoint, payload)
        return response

    def edit_domain_data(self, domain_id, new_domain, new_ip):
        # print(f"from edit_domain_data{domain_id},{new_domain},{new_ip}")
        # Prepare the data to be sent in the PUT request
        data = {
            "domain_id": domain_id,
            "domain_name": new_domain,
            "ip": new_ip
        }

        endpoint = "/api/user/user-domain/"

        # Send the PUT request to update the domain
        response = self.make_request('PUT', endpoint, data)

        return response

    def get_domain_report_data(self, user_id):
        """
        Fetch domain data from the external API using the API_PREFIX_VIZ from environment.
        Returns the response data if successful, otherwise raises an exception.
        """
        payload = {
           "user_id": user_id
        }
        endpoint = "/api/user/user-report-domain-det/"
        response = self.make_request('POST', endpoint, payload)

        if response.get("status") == 1:
            return {"status": 1, "domain": response.get("User_domain_details", [])}  # Success response
        else:
            return {"status": 0, "message": response.get("message", "DOMAIN DETAILS FETCHING FAILED")}
