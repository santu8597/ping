import os
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv

load_dotenv()
# Create your views here.
api_prefix_viz = os.getenv('API_URL_VIZ')
api_prefix_rd3 = os.getenv('API_URL_RD3')


class ProfileServices:
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

    def get_profile_report_data(self, user_id):
        """
        Fetch user profile data from the external API using the API_PREFIX_VIZ from environment.
        Returns the response data if successful, otherwise raises an exception.
        """
        payload = {
            "user_id": user_id
        }
        endpoint = "/api/user/user-report-profile-det/"
        response = self.make_request('POST', endpoint, payload)

        if response.get("status") == 1:
            return {"status": 1, "profile": response.get("User_profile_details", [])}  # Success response
        else:
            return {
                "status": 0,
                "message": response.get("message", "PROFILE DETAILS FETCHING FAILED")
            }
