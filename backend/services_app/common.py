from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from dotenv import load_dotenv
import os
import requests
from django.core.exceptions import ObjectDoesNotExist

# Subscription models removed from direct usage; features are stubbed.

load_dotenv()
# Create your views here.
api_prefix_viz = os.getenv('API_URL_VIZ')
api_prefix_rd3 = os.getenv('API_URL_RD3')


def token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get token from session
        token = request.session.get('token')
        if not token:
            # messages.error(request, "A Valid Token Is Missing.")
            return redirect('services_app:index')  # Redirect to login page if no token
        request.token = token  # Attach token to request object
        return view_func(request, *args, **kwargs)  # Call the view function with correct args

    return _wrapped_view


def get_profile_details(token: str):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    profile_details_api_url = api_prefix_viz + "/api/user/profile-details/"
    try:

        get_data = requests.get(profile_details_api_url, headers=headers)
        get_data.raise_for_status()
        try:

            response_data = get_data.json()

        except ValueError as e:

            return {
                'status': 'error',
                'message': f"Error: {str(e)}"
            }

        return {
            'status': 'success',
            'data': response_data["profile_details"][0]
        }
    except ValueError as e:

        return {
            'status': 'error',
            'message': f"Error: {str(e)}"
        }


def get_countries():
    countries_api_url = api_prefix_viz + "/api/common/country-list/"
    try:
        get_data = requests.get(countries_api_url)
        get_data.raise_for_status()
        try:
            response_data = get_data.json()

        except ValueError as e:

            return {
                'status': 'error',
                'message': f"Error: {str(e)}"
            }

        return response_data
    except ValueError as e:

        return {
            'status': 'error',
            'message': f"Error: {str(e)}"
        }


def get_cities():
    cities_api_url = api_prefix_viz + "/api/common/city-list/"
    try:

        get_data = requests.get(cities_api_url)
        get_data.raise_for_status()
        try:

            response_data = get_data.json()

        except ValueError as e:

            return {
                'status': 'error',
                'message': f"Error: {str(e)}"
            }

        return response_data

    except ValueError as e:

        return {
            'status': 'error',
            'message': f"Error: {str(e)}"
        }


def get_states():
    states_api_url = api_prefix_viz + "/api/common/state-list/"
    try:

        get_data = requests.get(states_api_url)
        get_data.raise_for_status()
        try:

            response_data = get_data.json()

        except ValueError as e:

            return {
                'status': 'error',
                'message': f"Error: {str(e)}"
            }

        return response_data
    except ValueError as e:

        return {
            'status': 'error',
            'message': f"Error: {str(e)}"
        }


def get_point_details(token: str):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    point_details_api_url = api_prefix_viz + "/api/common/features/"
    try:

        get_data = requests.get(point_details_api_url, headers=headers)
        get_data.raise_for_status()
        try:

            response_data = get_data.json()

        except ValueError as e:

            return {
                'status': 'error',
                'message': f"Error: {str(e)}"
            }

        return {
            'status': 'success',
            'data': response_data
        }
    except ValueError as e:

        return {
            'status': 'error',
            'message': f"Error: {str(e)}"
        }


def utilize_points_handler(
        anchor_user_id: int,
        command_name: str,
        run_time: int,
        utilize_point: int,
        token: str,
        anchor_user_ids: list = None,
):
    """
    Handler to utilize points for a command run.

    Args:
        anchor_user_id (int): The ID of the main user.
        command_name (str): The command that was run (e.g. "query").
        run_time (int): How long the command ran.
        utilize_point (int): Number of points to utilize.
        anchor_user_ids (list, optional): Additional user IDs.
        token (str): Bearer token for authorization.
    """
    if anchor_user_ids is None:
        anchor_user_ids = []

    headers = {'Authorization': f'Bearer {token}'}

    if not token:
        raise ValueError("Token is required!")

    if not api_prefix_viz or not headers:
        raise ValueError("Both 'api_prefix' and 'headers' are required.")

    point_data = {
        "anchor_user_id": anchor_user_id,
        "anchor_user_ids": anchor_user_ids,
        "command_name": command_name,
        "run_time": run_time,
        "utilize_point": utilize_point
    }

    # Subscription backend disabled: no-op and return a safe response.
    return {"status": 1, "message": "Points utilization skipped (subscription disabled)."}


def get_remaining_points_by_user(user_id):
    # Subscription model removed from direct usage — return zero remaining points
    # to indicate no subscription/points available. If you want a different
    # behavior (e.g., raise), change this implementation.
    return 0.0
