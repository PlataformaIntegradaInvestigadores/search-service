import logging
import threading

import requests
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.scopus_integration.application.services.model_corpus_observer_service import (
    ModelCorpusObserverService,
)
from apps.scopus_integration.application.services.scopus_client import ScopusClient
from apps.scopus_integration.application.usecases.scopus_integration_usecase import (
    ScopusIntegrationUseCase,
)

logger = logging.getLogger("django")


class ScopusIntegrationViewSet(viewsets.ModelViewSet):
    lock = threading.Lock()
    scopus_client = ScopusClient()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_corpus_observer = ModelCorpusObserverService()

    @extend_schema(
        summary="Integrate Scopus data",
        description=(
            "This endpoint integrates Scopus data. Optionally scoped to a "
            "single year via ?year=YYYY to fetch incrementally instead of "
            "the whole historical range in one request."
        ),
        parameters=[
            OpenApiParameter(
                name="year",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Fetch only this year's articles (e.g. 2021)",
                required=False,
            )
        ],
        tags=["Scopus Integration"],
    )
    def list(self, request, *args, **kwargs):
        # Se podria descomentar para tener solo una instancia corriendo
        # if not self.lock.acquire(blocking=False):
        #     return Response({"success": False, "message": "Another instance is already running."},
        #                     status=status.HTTP_429_TOO_MANY_REQUESTS)
        year = request.query_params.get("year")
        try:
            logger.log(logging.INFO, "Starting the Scopus integration .....")
            scopus_integration = ScopusIntegrationUseCase(
                scopus_client=self.scopus_client
            )
            scopus_integration.execute(year=year)
            return Response({"success": True}, status=status.HTTP_200_OK)
        except requests.HTTPError as e:
            error_content = e.response.json()
            error_message = error_content.get("error-response", {}).get(
                "error-message", ""
            )
            logger.log(logging.ERROR, error_message)
            return Response(
                {
                    "success": False,
                    "message": error_message,
                    "code": e.response.status_code,
                    "error": error_content,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.log(logging.ERROR, str(e))
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        finally:
            self.model_corpus_observer.delete_corpus()
            self.model_corpus_observer.delete_model()
            # self.lock.release()
