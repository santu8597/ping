# import requests

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status

# from config_env import CONFIG
 
# class RootvizProxyAPIView(APIView):

#     def get(self, request, filename, *args, **kwargs):

#         url = f"{CONFIG.ROOT_VIZ_URL}/root/{filename}/json/"  
 
#         try:

#             # Fetch data from external API

#             response = requests.get(url, timeout=10)
 
#             # Return raw JSON exactly as received

#             return Response(

#                 response.json(),

#                 status=response.status_code

#             )
 
#         except requests.exceptions.RequestException as e:

#             return Response(

#                 {"error": "Failed to fetch data", "details": str(e)},

#                 status=status.HTTP_502_BAD_GATEWAY

#             )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.utils.root_server import load_root_data

class RootvizDailyAPIView(APIView):

    def get(self, request):
        data = load_root_data()
        return Response(data, status=200)
