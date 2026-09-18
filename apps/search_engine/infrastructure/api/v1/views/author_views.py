from collections import OrderedDict

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.search_engine.application.services.affiliation_service import (
    AffiliationService,
)
from apps.search_engine.application.services.author_service import AuthorService
from apps.search_engine.application.usecases.affiliation.affiliations_by_authors_usecase import (
    AffiliationByAuthorsUsecase,
)
from apps.search_engine.application.usecases.author.author_by_affiliations_filters import (
    AuthorsByAffiliationsFiltersUseCase,
)
from apps.search_engine.application.usecases.author.author_by_id_usecase import (
    AuthorByIdUseCase,
)
from apps.search_engine.application.usecases.author.author_by_query_usecase import (
    AuthorByQueryUseCase,
)
from apps.search_engine.application.usecases.author.author_community_use_case import (
    AuthorsCommunityUseCase,
)
from apps.search_engine.application.usecases.author.list_all_authors_usecase import (
    ListAllAuthorsUseCase,
)
from apps.search_engine.application.usecases.author.most_relevant_authors_by_topic import (
    MostRelevantAuthorsByTopicUseCase,
)
from apps.search_engine.infrastructure.api.v1.serializers.affiliation_serializers import (
    AffiliationNameSerializer,
)
from apps.search_engine.infrastructure.api.v1.serializers.author_serializers import (
    AuthorSerializer,
    MostRelevantAuthorsRequestSerializer,
    RetrieveAuthorSerializer,
)
from apps.search_engine.infrastructure.api.v1.utils.build_paginator import (
    build_pagination_urls,
)


class AuthorViews(viewsets.ViewSet):
    # inject the service
    author_service = AuthorService()
    affiliation_service = AffiliationService()

    @extend_schema(
        description="List all authors",
        responses=AuthorSerializer(many=True),
        tags=["Authors"],
        parameters=[
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="page", type=int, required=False),
        ],
        summary="List all authors",
    )
    def list(self, request, *args, **kwargs):
        page_size = int(request.query_params.get("page_size", 10))
        page = int(request.query_params.get("page", 1))

        # inject use cases
        list_author_use_case = ListAllAuthorsUseCase(
            author_repository=self.author_service
        )

        # execute the use cases
        authors = list_author_use_case.execute(page_size=page_size, page=page)
        serializer = AuthorSerializer(authors, many=True)
        authors = serializer.data
        total = len(authors)
        data = authors
        pagination_info = build_pagination_urls(request, page, page_size, authors)

        return Response(
            {
                "total": total,
                "previous_page": pagination_info.get("previous_page"),
                "next_page": pagination_info.get("next_page"),
                "data": data,
            }
        )

    @extend_schema(
        description="Find authors by query",
        responses=RetrieveAuthorSerializer(many=True),
        tags=["Authors"],
        parameters=[
            OpenApiParameter(name="query", type=str, required=True),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="page", type=int, required=False),
        ],
        summary="Find authors by query",
    )
    @action(detail=False, methods=["get"], url_path="find_by_query")
    def find_by_query(self, request, *args, **kwargs):
        try:
            query = request.query_params.get("query", "")
            page_size = int(request.query_params.get("page_size", 10))
            page = int(request.query_params.get("page", 1))
            author_by_query_use_case = AuthorByQueryUseCase(
                author_repository=self.author_service
            )
            authors, total = author_by_query_use_case.execute(
                name=query, page_size=page_size, page=page
            )
            serializer = RetrieveAuthorSerializer(authors, many=True)
            pagination_info = build_pagination_urls(
                request, page, page_size, serializer.data
            )
            data = serializer.data
            return Response(
                {
                    "total": total,
                    "next_page": pagination_info.get("next_page"),
                    "previous_page": pagination_info.get("previous_page"),
                    "data": data,
                }
            )
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Retrieve an author by id",
        responses=AuthorSerializer,
        tags=["Authors"],
        summary="Retrieve an author by Scopus ID",
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            author_id = kwargs.get("pk")
            # Inject use case
            author_by_id_use_case = AuthorByIdUseCase(
                author_repository=self.author_service
            )
            author = author_by_id_use_case.execute(author_id)
            serializer = AuthorSerializer(author)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Most relevant authors",
        description="Retrieve an author by id",
        request=MostRelevantAuthorsRequestSerializer,
        tags=["Authors"],
        responses=AuthorSerializer,
        methods=["post"],
    )
    @action(detail=False, methods=["post"], url_path="most_relevant_authors")
    def most_relevant_authors(self, request, *args, **kwargs):
        try:
            serializer = MostRelevantAuthorsRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            topic = serializer.validated_data.get("topic")
            authors_number = serializer.validated_data.get("authors_number")
            custom_type = serializer.validated_data.get("type", None)
            custom_affiliations = serializer.validated_data.get("affiliations", [])
            most_relevant_authors_usecase = MostRelevantAuthorsByTopicUseCase(
                repository=self.author_service
            )
            affiliations_by_authors_usecase = AffiliationByAuthorsUsecase(
                repository=self.affiliation_service
            )
            authors_by_affiliation_filters_usecase = (
                AuthorsByAffiliationsFiltersUseCase(
                    author_repository=self.author_service
                )
            )
            author_community_use_case = AuthorsCommunityUseCase(
                author_repository=self.author_service
            )
            series = most_relevant_authors_usecase.execute(topic, authors_number)

            author_ids = series.index.to_list()
            affiliations = affiliations_by_authors_usecase.execute(author_ids)

            serializer = AffiliationNameSerializer(affiliations, many=True)
            serialized_data = serializer.data
            seen = OrderedDict()
            for affiliation in serialized_data:
                if affiliation["scopusId"] not in seen:
                    seen[affiliation["scopusId"]] = affiliation

            # Convertir de nuevo a una lista
            unique_serialized_data = list(seen.values())
            if custom_type is not None:
                filter_type = custom_type
                filter_affiliations = custom_affiliations
                filtered_authors = authors_by_affiliation_filters_usecase.execute(
                    filter_type, filter_affiliations, author_ids
                )
                filtered_ids = [author.scopus_id for author in filtered_authors]
                community = author_community_use_case.execute(filtered_ids)
                authors = community.get("nodes")
                links = community.get("links")
                size_nodes = community.get("size_nodes")
                size_links = community.get("size_links")
                author_serializer = AuthorSerializer(authors, many=True)

                community_data = {
                    "affiliations": unique_serialized_data,
                    "size_nodes": size_nodes,
                    "size_links": size_links,
                    "nodes": author_serializer.data,
                    "links": links,
                }
                return Response(community_data, status=status.HTTP_200_OK)
            else:
                community = author_community_use_case.execute(author_ids)
                authors = community.get("nodes")
                links = community.get("links")
                size_nodes = community.get("size_nodes")
                size_links = community.get("size_links")
                author_serializer = AuthorSerializer(authors, many=True)
                community_data = {
                    "affiliations": unique_serialized_data,
                    "size_nodes": size_nodes,
                    "size_links": size_links,
                    "nodes": author_serializer.data,
                    "links": links,
                }
                return Response(community_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
