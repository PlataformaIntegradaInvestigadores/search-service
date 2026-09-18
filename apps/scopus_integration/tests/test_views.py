"""Unitarias de las vistas de scopus_integration: GenerateCorpusView,
GenerateModelView, ScopusIntegrationViewSet, UpdateInformationViewSet,
DashboardInformationViewSet, LoggerViewSet y EtlRunView.

Todas las vistas que tocan ModelCorpusObserverService (borra el modelo/
corpus TF-IDF de produccion en su `finally`) o ModelGenerationService
(lee/escribe el pickle de produccion) se mockean por completo: nunca deben
tocar resources/models o resources/corpus reales."""

import threading
from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from apps.scopus_integration.infrastructure.api.v1.views.corpus_modeling_views import (
    GenerateCorpusView,
)
from apps.scopus_integration.infrastructure.api.v1.views.dashboard_information_views import (
    DashboardInformationViewSet,
)
from apps.scopus_integration.infrastructure.api.v1.views.etl_views import EtlRunView
import apps.scopus_integration.infrastructure.api.v1.views.etl_views as etl_views_module
from apps.scopus_integration.infrastructure.api.v1.views.logger_views import (
    LoggerViewSet,
)
from apps.scopus_integration.infrastructure.api.v1.views.model_generation_views import (
    GenerateModelView,
)
from apps.scopus_integration.infrastructure.api.v1.views.scopus_integration_views import (
    ScopusIntegrationViewSet,
)
from apps.scopus_integration.infrastructure.api.v1.views.update_information_views import (
    UpdateInformationViewSet,
)

VIEWS = "apps.scopus_integration.infrastructure.api.v1.views"


class GenerateCorpusViewTests(APITestCase):
    def test_genera_corpus_y_guarda_pickle_mockeado(self):
        request = APIRequestFactory().post("/generate-corpus/")
        data = [{"doc_id": "1", "doc": "Hola Mundo, esto es una prueba."}]

        with patch(f"{VIEWS}.corpus_modeling_views.GenerateCorpusUseCase") as mock_uc:
            mock_uc.return_value.execute.return_value = data
            with patch("pandas.DataFrame.to_pickle"):
                with patch(
                    "pandas.read_pickle",
                    return_value=__import__("pandas").DataFrame(data),
                ):
                    response = GenerateCorpusView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["total"], 1)

    def test_error_retorna_400(self):
        request = APIRequestFactory().post("/generate-corpus/")

        with patch(
            f"{VIEWS}.corpus_modeling_views.GenerateCorpusUseCase",
            side_effect=RuntimeError("boom"),
        ):
            response = GenerateCorpusView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])


class GenerateModelViewTests(APITestCase):
    def test_genera_modelo_mockeando_disco(self):
        request = APIRequestFactory().post("/generate-model/")

        with patch(f"{VIEWS}.model_generation_views.ModelGenerationService") as mock_svc:
            mock_instance = mock_svc.return_value
            mock_instance.read_path.return_value = {"preprocessed_doc": []}
            response = GenerateModelView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_instance.generate_model.assert_called_once()

    def test_error_retorna_400(self):
        request = APIRequestFactory().post("/generate-model/")

        with patch(
            f"{VIEWS}.model_generation_views.ModelGenerationService",
            side_effect=RuntimeError("boom"),
        ):
            response = GenerateModelView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ScopusIntegrationViewSetTests(APITestCase):
    def test_list_ejecuta_integracion_y_limpia_modelo_corpus(self):
        request = APIRequestFactory().get("/scopus-integration/")

        with patch(f"{VIEWS}.scopus_integration_views.ScopusIntegrationUseCase") as mock_uc:
            with patch(
                f"{VIEWS}.scopus_integration_views.ModelCorpusObserverService"
            ) as mock_observer_cls:
                mock_observer = mock_observer_cls.return_value
                response = ScopusIntegrationViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_uc.return_value.execute.assert_called_once()
        mock_observer.delete_corpus.assert_called_once()
        mock_observer.delete_model.assert_called_once()

    def test_http_error_extrae_mensaje_de_scopus(self):
        import requests

        request = APIRequestFactory().get("/scopus-integration/")
        fake_response = MagicMock()
        fake_response.json.return_value = {
            "error-response": {"error-message": "Rate limit"}
        }
        fake_response.status_code = 429
        http_error = requests.HTTPError(response=fake_response)

        with patch(
            f"{VIEWS}.scopus_integration_views.ScopusIntegrationUseCase"
        ) as mock_uc:
            mock_uc.return_value.execute.side_effect = http_error
            with patch(f"{VIEWS}.scopus_integration_views.ModelCorpusObserverService"):
                response = ScopusIntegrationViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["message"], "Rate limit")

    def test_excepcion_generica_retorna_400(self):
        request = APIRequestFactory().get("/scopus-integration/")

        with patch(
            f"{VIEWS}.scopus_integration_views.ScopusIntegrationUseCase"
        ) as mock_uc:
            mock_uc.return_value.execute.side_effect = RuntimeError("boom")
            with patch(f"{VIEWS}.scopus_integration_views.ModelCorpusObserverService"):
                response = ScopusIntegrationViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateInformationViewSetTests(APITestCase):
    def test_actualiza_autores_y_limpia_modelo_corpus(self):
        request = APIRequestFactory().post("/update/author-information/")

        with patch(
            f"{VIEWS}.update_information_views.UpdateAuthorInformationUseCase"
        ) as mock_uc:
            mock_uc.return_value.execute.return_value = 5
            with patch(
                f"{VIEWS}.update_information_views.ModelCorpusObserverService"
            ) as mock_observer_cls:
                mock_observer = mock_observer_cls.return_value
                view = UpdateInformationViewSet.as_view(
                    {"post": "update_author_information"}
                )
                response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("5 Authors", response.data["message"])
        mock_observer.delete_corpus.assert_called_once()

    def test_ya_en_ejecucion_retorna_429(self):
        request = APIRequestFactory().post("/update/author-information/")

        with patch.object(UpdateInformationViewSet, "lock", threading.Lock()) as lock:
            lock.acquire()
            try:
                with patch(
                    f"{VIEWS}.update_information_views.ModelCorpusObserverService"
                ):
                    view = UpdateInformationViewSet.as_view(
                        {"post": "update_author_information"}
                    )
                    response = view(request)
            finally:
                lock.release()

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_http_error_extrae_mensaje(self):
        import json

        import requests

        request = APIRequestFactory().post("/update/author-information/")
        fake_response = MagicMock()
        fake_response.text = json.dumps(
            {"error-response": {"error-message": "Quota exceeded"}}
        )
        fake_response.status_code = 429
        http_error = requests.HTTPError(response=fake_response)

        with patch(
            f"{VIEWS}.update_information_views.UpdateAuthorInformationUseCase"
        ) as mock_uc:
            mock_uc.return_value.execute.side_effect = http_error
            with patch(f"{VIEWS}.update_information_views.ModelCorpusObserverService"):
                view = UpdateInformationViewSet.as_view(
                    {"post": "update_author_information"}
                )
                response = view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["message"], "Quota exceeded")

    def test_excepcion_generica_retorna_500(self):
        request = APIRequestFactory().post("/update/author-information/")

        with patch(
            f"{VIEWS}.update_information_views.UpdateAuthorInformationUseCase"
        ) as mock_uc:
            mock_uc.return_value.execute.side_effect = RuntimeError("boom")
            with patch(f"{VIEWS}.update_information_views.ModelCorpusObserverService"):
                view = UpdateInformationViewSet.as_view(
                    {"post": "update_author_information"}
                )
                response = view(request)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardInformationViewSetTests(APITestCase):
    def _view(self, method_map):
        return DashboardInformationViewSet.as_view(method_map)

    def test_get_authors_comparator(self):
        request = APIRequestFactory().get("/dashboard/information/get_authors_comparator/")
        vs = DashboardInformationViewSet()
        vs.author_service = MagicMock(
            get_authors_no_updated_count=MagicMock(return_value=3),
            authors_count=MagicMock(return_value=100),
        )
        with patch.object(
            DashboardInformationViewSet, "author_service", vs.author_service
        ):
            response = self._view({"get": "get_authors_comparator"})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["authors_no_updated"], 3)
        self.assertEqual(response.data["total_authors"], 100)

    def test_get_authors_comparator_error_retorna_400(self):
        request = APIRequestFactory().get("/dashboard/information/get_authors_comparator/")
        with patch.object(
            DashboardInformationViewSet,
            "author_service",
            MagicMock(
                get_authors_no_updated_count=MagicMock(side_effect=RuntimeError("x"))
            ),
        ):
            response = self._view({"get": "get_authors_comparator"})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_articles_comparator(self):
        request = APIRequestFactory().get("/dashboard/information/get_articles_comparator/")
        with patch.object(
            DashboardInformationViewSet,
            "article_service",
            MagicMock(articles_count=MagicMock(return_value=50)),
        ), patch.object(
            DashboardInformationViewSet,
            "retrieve_scopus_data",
            MagicMock(get_total_articles_from_scopus=MagicMock(return_value="60")),
        ):
            response = self._view({"get": "get_articles_comparator"})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_centinela"], 50)
        self.assertEqual(response.data["total_scopus"], 60)

    def test_tfidf_model_corpus(self):
        request = APIRequestFactory().get("/dashboard/information/tfidf_model_corpus/")
        with patch.object(
            DashboardInformationViewSet,
            "model_corpus_observer",
            MagicMock(
                verify_model_path_exists=MagicMock(return_value=True),
                verify_corpus_path_exists=MagicMock(return_value=False),
            ),
        ):
            response = self._view({"get": "tfidf_model_corpus"})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"model": True, "corpus": False})

    def test_get_system_health_calcula_stale_collections(self):
        request = APIRequestFactory().get("/dashboard/information/get_system_health/")
        with patch.object(
            DashboardInformationViewSet,
            "author_service",
            MagicMock(
                get_authors_no_updated_count=MagicMock(return_value=1),
                authors_count=MagicMock(return_value=10),
            ),
        ), patch.object(
            DashboardInformationViewSet,
            "article_service",
            MagicMock(articles_count=MagicMock(return_value=20)),
        ), patch.object(
            DashboardInformationViewSet,
            "affiliation_service",
            MagicMock(find_total_affiliations=MagicMock(return_value=5)),
        ), patch.object(
            DashboardInformationViewSet,
            "topic_service",
            MagicMock(topics_count=MagicMock(return_value=7)),
        ), patch(f"{VIEWS}.dashboard_information_views.MongoAuthor") as mongo_author, patch(
            f"{VIEWS}.dashboard_information_views.MongoAffiliation"
        ) as mongo_affil, patch(
            f"{VIEWS}.dashboard_information_views.CountryTopics"
        ) as mongo_topics, patch(
            f"{VIEWS}.dashboard_information_views.CountryAcumulated"
        ) as mongo_acum:
            mongo_author.objects.count.return_value = 9
            mongo_affil.objects.count.return_value = 5
            mongo_topics.objects.filter.return_value.filter.return_value.count.return_value = 7
            mongo_acum.objects.order_by.return_value.first.return_value = MagicMock(
                total_articles=18
            )

            response = self._view({"get": "get_system_health"})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["articles_pending"], 2)
        self.assertIn("author", response.data["stale_collection_names"])
        self.assertIn("country_acumulated", response.data["stale_collection_names"])
        self.assertNotIn("affiliation", response.data["stale_collection_names"])

    def test_get_system_health_error_retorna_400(self):
        request = APIRequestFactory().get("/dashboard/information/get_system_health/")
        with patch.object(
            DashboardInformationViewSet,
            "author_service",
            MagicMock(
                get_authors_no_updated_count=MagicMock(side_effect=RuntimeError("x"))
            ),
        ):
            response = self._view({"get": "get_system_health"})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoggerViewSetTests(APITestCase):
    def test_list_filtra_por_nivel_y_pagina(self, *_):
        import glob

        request = APIRequestFactory().get(
            "/admin/logs/", {"level": "ERROR", "page": "1", "lines_per_page": "1"}
        )
        fake_lines = ["2024-01-01 INFO ok\n", "2024-01-02 ERROR bad\n"]

        with patch("glob.glob", return_value=["fake.log"]):
            with patch("builtins.open", __import__("unittest.mock", fromlist=["mock_open"]).mock_open(
                read_data="".join(fake_lines)
            )) as m:
                m.return_value.readlines.return_value = fake_lines
                response = LoggerViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_lines"], 1)
        self.assertIn("ERROR", response.data["logs"][0])

    def test_list_sin_filtros_retorna_todo_paginado(self):
        fake_lines = ["2024-01-01 INFO ok\n", "2024-01-02 DEBUG other\n"]
        request = APIRequestFactory().get("/admin/logs/")

        with patch("glob.glob", return_value=["fake.log"]):
            with patch("builtins.open", __import__("unittest.mock", fromlist=["mock_open"]).mock_open()) as m:
                m.return_value.readlines.return_value = fake_lines
                response = LoggerViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_lines"], 2)

    def test_list_error_retorna_400(self):
        request = APIRequestFactory().get("/admin/logs/")

        with patch("glob.glob", side_effect=RuntimeError("boom")):
            response = LoggerViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EtlRunViewTests(APITestCase):
    def setUp(self):
        etl_views_module._etl_running = False
        etl_views_module._last_run_at = None
        etl_views_module._last_run_status = None
        if etl_views_module._etl_lock.locked():
            etl_views_module._etl_lock.release()

    def test_post_lanza_etl_en_background_y_retorna_202(self):
        request = APIRequestFactory().post("/admin/etl/run/")
        done = threading.Event()

        def fake_call_command(name):
            done.set()

        with patch(f"{VIEWS}.etl_views.call_command", side_effect=fake_call_command):
            response = EtlRunView.as_view()(request)
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            done.wait(timeout=5)
            import time

            time.sleep(0.05)

        self.assertEqual(etl_views_module._last_run_status, "success")

    def test_post_si_ya_esta_corriendo_retorna_409(self):
        request = APIRequestFactory().post("/admin/etl/run/")
        etl_views_module._etl_lock.acquire()
        try:
            response = EtlRunView.as_view()(request)
        finally:
            etl_views_module._etl_lock.release()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_get_reporta_estado_idle(self):
        request = APIRequestFactory().get("/admin/etl/run/")
        response = EtlRunView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "idle")

    def test_post_falla_marca_estado_error(self):
        request = APIRequestFactory().post("/admin/etl/run/")
        done = threading.Event()

        def fake_call_command(name):
            done.set()
            raise RuntimeError("etl boom")

        with patch(f"{VIEWS}.etl_views.call_command", side_effect=fake_call_command):
            EtlRunView.as_view()(request)
            done.wait(timeout=5)
            import time

            time.sleep(0.05)

        self.assertEqual(etl_views_module._last_run_status, "error")
