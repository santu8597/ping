import os
import requests
from requests.exceptions import RequestException
from dotenv import load_dotenv
from datetime import datetime, timezone
from dateutil import parser

load_dotenv()
# Create your views here.
api_prefix_viz = os.getenv('API_URL_VIZ')
api_prefix_rd3 = os.getenv('API_URL_RD3')


class ZoneServices:
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
            elif method == "PUT":
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

    def get_time(self, zone_response):
        zones = zone_response.get("zone", [])
        created_dates = [parser.isoparse(z.get("created_date")) for z in zones if z.get("created_date")]
        if not created_dates:
            return None, None, None

        latest_time = max(created_dates)
        now = datetime.now(timezone.utc)
        diff = now - latest_time

        minutes = int(diff.total_seconds() // 60)
        if minutes < 1:
            readable_diff = "just now"
        elif minutes < 60:
            readable_diff = f"{minutes} minutes ago"
        elif minutes < 1440:
            hours = minutes // 60
            readable_diff = f"{hours} hours ago"
        else:
            days = minutes // 1440
            readable_diff = f"{days} days ago"

        return latest_time.isoformat(), now.isoformat(), readable_diff

    def get_zone_data(self, include_time=False):
        """
        Fetch zone data from the external API using the API_PREFIX_VIZ from environment.
        Returns the response data if successful. If include_time is True, calculates and includes time diff.
        """
        endpoint = "/api/user/user-zone/"
        response = self.make_request('GET', endpoint)

        
        if include_time:
            latest_time, current_time, diff_str = self.get_time(response)
            return {
                "zone_data": response.get("zone", []),
                "latest_time": latest_time,
                "current_time": current_time,
                "time_diff": diff_str
            }

        return response

    def add_zone_data(self, anchor_ids, zone):
        """
        Adds domain data to the external API.
        Sends the zone + anchor list to the external API.
        Prints the payload for verification.
        Returns {"status": 1} on success or {"status":0, "message":...} on failure.
        """


        anchor_ids = [int(a) for a in anchor_ids]
        payload = {
            "zone_name": zone,
            "user_anchor_ids": anchor_ids  # <- **flat list**, not nested
        }
        endpoint = "/api/user/user-zone/"
        response = self.make_request("POST", endpoint, payload)

        if response.get("status") == 1:
            return {"status": 1}  # Success response
        else:
            return {
                "status": 0,
                "message": response.get("message", "ZONE ADDITION FAILED"),
            }

    def delete_zone_data(self, zone_id):
        """
        Sends {"zone_id": zone_id, "is_delete": true} to the external API.
        Prints the ID in terminal for debug.
        """
        # print("delete_zone_data called → zone_id:", zone_id)

        payload = {
            "is_delete": True,
            "zone_id": zone_id
        }
        endpoint = "/api/user/user-zone/"

        response = self.make_request("PUT", endpoint, payload)

        if response.get("status") == 1:
            return {"status": 1}
        else:
            return {
                "status": 0,
                "message": response.get("message", "ZONE DELETE FAILED")
            }
    def get_zone_report_data(self, user_id):
        """
        Fetch zone data from the external API using the API_PREFIX_VIZ from environment.
        Returns the response data if successful, otherwise raises an exception.
        """
        payload = {
           "user_id": user_id
        }
        endpoint = "/api/user/user-report-zone-det/"
        response = self.make_request('POST', endpoint, payload)

        if response.get("status") == 1:
            return {"status": 1, "zone": response.get("User_zone_details", [])}  # Success response
        else:
            return {"status": 0, "message": response.get("message", "ZONE DETAILS FETCHING FAILED")}
