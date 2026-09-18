from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.search_engine.application.services.affiliation_service import (
    AffiliationService,
)
from apps.search_engine.application.usecases.affiliation.find_affiliation_by_id import (
    FindAffiliationByScopusIdIUseCase,
)
from apps.search_engine.application.usecases.affiliation.list_all_affiliation_usecase import (
    ListAllAffiliationsUseCase,
)
from apps.search_engine.application.usecases.affiliation.total_affiliations_usecase import (
    TotalAffiliationsUseCase,
)
from apps.search_engine.infrastructure.api.v1.serializers.affiliation_serializers import (
    AffiliationSerializer,
)
from apps.search_engine.infrastructure.api.v1.utils.build_paginator import (
    build_pagination_urls,
)


class AffiliationViewSet(viewsets.ViewSet):
    serializer_class = AffiliationSerializer

    affiliation_service = AffiliationService()

    @extend_schema(
        description="List all affiliations",
        responses=AffiliationSerializer(many=True),
        tags=["Affiliations"],
        parameters=[
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Page number",
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Page size",
            ),
        ],
        summary="List all affiliations",
    )
    def list(self, request, *args, **kwargs):
        try:
            page_number = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 10))

            # Inject the use cases
            list_affiliation_use_case = ListAllAffiliationsUseCase(
                affiliation_repository=self.affiliation_service
            )
            total_affiliations_use_case = TotalAffiliationsUseCase(
                affiliation_repository=self.affiliation_service
            )

            # Execute the use cases
            affiliations = list_affiliation_use_case.execute(page_number, page_size)
            total_affiliations = total_affiliations_use_case.execute()

            serializer = AffiliationSerializer(affiliations, many=True)
            pagination_info = build_pagination_urls(
                request, page_number, page_size, affiliations
            )

            return Response(
                {
                    "total": total_affiliations,
                    "next_page": pagination_info.get("next_page"),
                    "previous_page": pagination_info.get("previous_page"),
                    "results": serializer.data,
                }
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Retrieve an affiliation by Scopus ID",
        responses=AffiliationSerializer,
        tags=["Affiliations"],
        summary="Retrieve an affiliation by Scopus ID",
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            affiliation_id = kwargs.get("pk")

            # Inject the use cases
            get_affiliation_use_case = FindAffiliationByScopusIdIUseCase(
                affiliation_repository=self.affiliation_service
            )

            # Execute the use cases
            affiliation = get_affiliation_use_case.execute(affiliation_id)

            serializer = AffiliationSerializer(affiliation)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
