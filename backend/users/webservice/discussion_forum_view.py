from django.http import JsonResponse
from backend.users.serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Max, Count, Sum, Avg
from django.shortcuts import get_object_or_404
from backend.users.models import DiscussionVote, ReplyVote
import google.generativeai as genai
from openai import OpenAI
from services.email_service import EmailHelper
from django.conf import settings
from config_env import CONFIG
from dotenv import load_dotenv
import requests
from django.db.models import Prefetch
from backend.utils.helpers import get_cache, set_cache

load_dotenv()

# Discussion forum API disabled. The classes below return a 410 response
# to keep routes intact (non-destructive removal).

class DiscussionCategoriesView(APIView):
    def get(self, request):
        return JsonResponse({"status": 0, "msg": "Discussion feature disabled."}, status=410)

    def post(self, request):
        return JsonResponse({"status": 0, "msg": "Discussion feature disabled."}, status=410)

    def put(self, request):
        return JsonResponse({"status": 0, "msg": "Discussion feature disabled."}, status=410)


class ContributorsView(APIView):
    def get(self, request):
        return JsonResponse({"status": 0, "msg": "Discussion feature disabled."}, status=410)


class DiscussionView(APIView):
    def get(self, request, topicid=None):
        return JsonResponse({"status": 0, "msg": "Discussion feature disabled."}, status=410)

    def post(self, request):
        return JsonResponse({"status": 0, "msg": "Discussion feature disabled."}, status=410)


class GetAISummaryView(APIView):
    def get(self, request, cat_id=None):
        return JsonResponse({"status": 0, "msg": "AI summary (discussions) disabled."}, status=410)


class VoteDiscussionAPI(APIView):
    def post(self, request, discussion_id=None):
        return JsonResponse({"status": 0, "msg": "Voting disabled (discussions removed)."}, status=410)


class VoteReplyAPI(APIView):
    def post(self, request, reply_id=None):
        return JsonResponse({"status": 0, "msg": "Voting disabled (discussions removed)."}, status=410)

