from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.dashboards.domain.entities.author_topics import AuthorTopics
from apps.dashboards.domain.entities.author_year import AuthorYear
from apps.dashboards.infrastructure.api.v1.serializers.author_topics_serializer import (
    AuthorTopicsSerializer,
)
from apps.dashboards.infrastructure.api.v1.serializers.author_year_serializer import (
    AuthorYearSerializer,
)


class AuthorViews(viewsets.ModelViewSet):

    @extend_schema(
        description="Get author publication years",
        responses=AuthorYearSerializer(many=True),
        tags=["Authors"],
        parameters=[
            OpenApiParameter(
                name="scopus_id",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Scopus ID",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_author_years(self, request):
        try:
            scopus_id = request.query_params.get("scopus_id")
            author = (
                AuthorYear.objects(scopus_id=scopus_id)
                .filter(year__gt=1999)
                .order_by("year")
            )
            serializer = AuthorYearSerializer(author, many=True)
            data = serializer.data
            return Response(data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get topics associated with an author",
        responses=AuthorTopicsSerializer(many=True),
        tags=["Authors"],
        parameters=[
            OpenApiParameter(
                name="scopus_id",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Scopus ID",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_topics(self, request):
        try:
            scopus_id = request.query_params.get("scopus_id")
            author_topics = (
                AuthorTopics.objects(scopus_id=scopus_id)
                .filter(topic_name__ne=" ")
                .filter(topic_name__ne="")
                .order_by("-total_articles")
            )
            response_data = [
                {"text": topic["topic_name"], "size": topic["total_articles"]}
                for topic in author_topics
            ]
            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
