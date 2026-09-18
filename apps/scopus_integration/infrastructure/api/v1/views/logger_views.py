import glob
import os

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.scopus_integration.infrastructure.api.v1.serializers.logger_request_serializer import (
    LoggerRequestSerializer,
)


class LoggerViewSet(viewsets.ViewSet):
    serializer_class = LoggerRequestSerializer

    @extend_schema(
        description="List all logs",
        tags=["Logs"],
        parameters=[
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Page number",
            ),
            OpenApiParameter(
                name="lines_per_page",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Lines per page",
            ),
            OpenApiParameter(
                name="level",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Log level (e.g., DEBUG, INFO, ERROR)",
            ),
            OpenApiParameter(
                name="start_date",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Start date in YYYY-MM-DD format",
            ),
            OpenApiParameter(
                name="end_date",
                type=str,
                location=OpenApiParameter.QUERY,
                description="End date in YYYY-MM-DD format",
            ),
            OpenApiParameter(
                name="keyword",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Keyword to search in logs",
            ),
        ],
        summary="List all logs",
    )
    def list(self, request, *args, **kwargs):
        try:
            page = int(request.query_params.get("page", 1))
            lines_per_page = int(request.query_params.get("lines_per_page", 10))
            log_level = request.query_params.get("level", None)
            start_date = request.query_params.get("start_date", None)
            end_date = request.query_params.get("end_date", None)
            keyword = request.query_params.get("keyword", None)

            log_dir = "centinela_logs/"
            log_pattern = os.path.join(log_dir, "info.log*")
            log_files = glob.glob(log_pattern)
            filtered_logs = []

            for log_file in sorted(log_files):
                with open(log_file, encoding="utf-8") as file:
                    lines = file.readlines()
                    for line in lines:
                        if log_level and log_level not in line:
                            continue
                        if start_date or end_date:
                            log_date = line.split(" ")[0]
                            if start_date and log_date < start_date:
                                continue
                            if end_date and log_date > end_date:
                                continue
                        if keyword and keyword not in line:
                            continue
                        filtered_logs.append(line)

            filtered_logs.reverse()

            total_lines = len(filtered_logs)
            start = (page - 1) * lines_per_page
            end = page * lines_per_page
            if end > total_lines:
                end = total_lines

            return Response(
                {
                    "page": page,
                    "lines_per_page": lines_per_page,
                    "total_lines": total_lines,
                    "logs": filtered_logs[start:end],
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
