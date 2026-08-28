from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.dashboards.application.services.province_service import ProvinceService
from apps.dashboards.application.use_cases.get_provinces import ProvincesUseCase
from apps.dashboards.application.use_cases.get_provinces_acumulated_year import (
    ProvincesAcumulatedUseCase,
)
from apps.dashboards.application.use_cases.get_provinces_year_use_case import (
    ProvincesYearUseCase,
)
from apps.dashboards.infrastructure.api.v1.serializers.province_acumulated_serializer import (
    ProvinceAcumulatedSerializer,
)
from apps.dashboards.infrastructure.api.v1.serializers.province_serializer import (
    ProvinceSerializer,
)
from apps.dashboards.infrastructure.api.v1.serializers.province_year_serializer import (
    ProvinceYearSerializer,
)


class ProvinceViews(viewsets.ModelViewSet):
    province_service = ProvinceService()

    @extend_schema(
        description="Get all provinces",
        responses=ProvinceSerializer(many=True),
        tags=["Provinces"],
    )
    @action(detail=False, methods=["get"])
    def get_provinces(self, request):
        try:
            provinces_use_case = ProvincesUseCase(
                province_service=self.province_service
            )
            data_provinces = provinces_use_case.execute()
            serializer = ProvinceSerializer(data_provinces, many=True)
            response = serializer.data
            return Response(response)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get provinces data by year",
        responses=ProvinceYearSerializer(many=True),
        tags=["Provinces"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_provinces_year(self, request):
        try:
            year = request.query_params.get("year")
            year_use_case = ProvincesYearUseCase(province_service=self.province_service)
            year_data = year_use_case.execute(year=year)
            serializer = ProvinceYearSerializer(year_data, many=True)
            response = serializer.data
            return Response(response)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        description="Get accumulated provinces data by year",
        responses=ProvinceAcumulatedSerializer(many=True),
        tags=["Provinces"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Year",
            )
        ],
    )
    @action(detail=False, methods=["get"])
    def get_provinces_acumulated(self, request):
        try:
            year = request.query_params.get("year")
            year_use_case = ProvincesAcumulatedUseCase(
                province_service=self.province_service
            )
            year_data = year_use_case.execute(year=year)
            serializer = ProvinceAcumulatedSerializer(year_data, many=True)
            response = serializer.data
            return Response(response)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

