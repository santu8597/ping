from django.shortcuts import render
from django.db.models import Count, Case, When, Value, CharField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated  # adjust as needed
from .models import CommendExecutionHistory
from .serializers import QueryStatsSerializer


# Create your views here.


class QueryStatsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        qs = CommendExecutionHistory.objects.filter(is_deleted=False)

        total_query_count = qs.count()

        # Group by query field
        query_stats = (
            qs.values("query")
              .annotate(total_queries=Count("id"))
              .order_by("query")
        )

        # Convert None or empty "query" to "other"
        for item in query_stats:
            if not item["query"]:
                item["query"] = "other"

        serializer = QueryStatsSerializer(query_stats, many=True)

        return Response({
            "total_query_count": total_query_count,
            "stats": serializer.data
        })



