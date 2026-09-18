from drf_spectacular.utils import extend_schema
from neomodel import DoesNotExist
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.search_engine.application.services.author_service import AuthorService
from apps.search_engine.application.services.coauthored_service import CoAuthoredService
from apps.search_engine.application.usecases.coauthored.find_coauthors_by_id_usecase import (
    FindCoauthorsByIdUsecase,
)
from apps.search_engine.infrastructure.api.v1.serializers.author_serializers import (
    AuthorCoAuthorSerializer,
)


class CoAuthorsViewSet(viewsets.ViewSet):
    # Inject the service
    author_service = AuthorService()
    co_author_service = CoAuthoredService(author_repository=author_service)

    @extend_schema(
        description="Find coauthors by author id",
        tags=["Coauthors"],
        responses={"data": "data"},
        summary="Find coauthors by author id",
    )
    @action(detail=True, methods=["get"], url_path="")
    def coauthors_by_id(self, request, *args, **kwargs):
        try:
            author_id = kwargs.get("pk")
            find_coauthors_use_case = FindCoauthorsByIdUsecase(
                coauthor_repository=self.co_author_service
            )
            coauthors, links = find_coauthors_use_case.execute(author_id)
            serializer = AuthorCoAuthorSerializer(coauthors, many=True)
            data = {"nodes": serializer.data, "links": links}
            return Response({"data": data})
        except DoesNotExist:
            return Response({"error": "Author not found."})
        except Exception as e:
            return Response({"error": str(e)})
