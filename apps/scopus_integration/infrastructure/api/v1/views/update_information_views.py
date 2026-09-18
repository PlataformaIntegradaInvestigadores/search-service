import json
import threading

import requests
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.scopus_integration.application.services.model_corpus_observer_service import (
    ModelCorpusObserverService,
)
from apps.scopus_integration.application.services.scopus_client import ScopusClient
from apps.scopus_integration.application.usecases.update_author_information_usecase import (
    UpdateAuthorInformationUseCase,
)
from apps.search_engine.application.services.author_service import AuthorService


class UpdateInformationViewSet(viewsets.ViewSet):
    client = ScopusClient()
    author_repository = AuthorService()
    lock = threading.Lock()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_corpus_observer = ModelCorpusObserverService()

    @extend_schema(
        summary="Update author information",
        description="This endpoint updates the author information.",
        tags=["Scopus Integration"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="author-information",
        url_name="update-author-information",
    )
    def update_author_information(self, request, *args, **kwargs):
        if not self.lock.acquire(blocking=False):
            return Response(
                {"success": False, "message": "Another instance is already running."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        try:
            update_author_information_usecase = UpdateAuthorInformationUseCase(
                author_repository=self.author_repository, client=self.client
            )
            total = update_author_information_usecase.execute()
            return Response(
                {
                    "success": True,
                    "message": f"{total} Authors were updated successfully",
                },
                status=status.HTTP_200_OK,
            )
        except requests.HTTPError as e:
            error_content = json.loads(e.response.text)
            error_message = error_content.get("error-response", {}).get(
                "error-message", ""
            )
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
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        finally:
            self.model_corpus_observer.delete_corpus()
            self.model_corpus_observer.delete_model()
            self.lock.release()
