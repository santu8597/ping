import json
import requests
from django.http import HttpRequest
import os

api_prefix_viz = os.getenv('API_URL_VIZ')


def get_client_ip(request):
    """ Get the client's real IP address """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    # print("raw ip data..............", x_forwarded_for)
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]  # Get the first IP in the list
    else:
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")  # Direct IP address
    return ip


# Main function to send IP data to API
def send_ip_data(request: HttpRequest):
    # Get the client IP address
    ip_address = get_client_ip(request)

    # Prepare data
    data = {
        "ip": ip_address,
        "serve": "localhost"
    }
    json_data = json.dumps(data)

    # API endpoint
    url = api_prefix_viz + "/api/anchor/serve-measurement/"

    try:
        # Make POST request
        response = requests.post(url, data=json_data, headers={"Content-Type": "application/json"})
        response.raise_for_status()

        # Decode response
        response_data = response.json()
        return response_data

    except requests.exceptions.RequestException as e:
        # Log or handle exception
        print(f"Request failed: {e}")
        return None
