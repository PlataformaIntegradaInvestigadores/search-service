from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.search_engine.application.services.topic_service import TopicService
from apps.search_engine.application.usecases.topic.list_all_topics_usecase import (
    ListAllTopicsUseCase,
)
from apps.search_engine.infrastructure.api.v1.serializers.topic_serializer import (
    TopicSerializer,
)


class TopicViewSet(viewsets.ViewSet):
    # Inject Service
    topic_service = TopicService()

    @extend_schema(
        summary="Get all topics",
        responses={200: TopicSerializer(many=True)},
        tags=["Topics"],
    )
    def list(self, request, *args, **kwargs):
        try:
            # Inject use case
            list_all_topics = ListAllTopicsUseCase(topic_repository=self.topic_service)
            topics = list_all_topics.execute()
            serializer = TopicSerializer(topics, many=True)
            return Response({"topics": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            raise Exception(f"Error: {e}")
