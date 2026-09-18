from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.search_engine.application.services.article_service import ArticleService
from apps.search_engine.application.services.author_service import AuthorService
from apps.search_engine.application.services.topic_service import TopicService
from apps.search_engine.application.usecases.summary.get_summary_usecase import (
    GetSummaryUseCase,
)


class SummaryView(APIView):
    author_service = AuthorService()
    topic_service = TopicService()
    article_service = ArticleService()

    @extend_schema(
        summary="Get summary",
        tags=["Summary"],
    )
    def get(self, request, *args, **kwargs):
        try:
            summary_use_case = GetSummaryUseCase(
                self.article_service, self.author_service, self.topic_service
            )
            data = summary_use_case.execute()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
