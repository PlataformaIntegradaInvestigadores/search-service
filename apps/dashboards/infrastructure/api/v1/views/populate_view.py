from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboards.application.services.populate_service import PopulateService
from apps.dashboards.application.use_cases.populate_use_case import PopulateUseCase


class PopulateView(APIView):
    populate_service = PopulateService()

    @extend_schema(
        description="Populate the datalake with data",
        responses={
            200: OpenApiResponse(
                description="Datalake populated successfully",
                examples={"application/json": {"message": "datalake populated"}},
            ),
            500: OpenApiResponse(
                description="Internal Server Error",
                examples={"application/json": {"error": "error message"}},
            ),
        },
        tags=["Data Population"],
    )
    def post(self, request):
        try:
            populate_use_case = PopulateUseCase(populate_service=self.populate_service)
            populate_use_case.execute()
            return Response(
                {"message": "Analytics DB populated"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

