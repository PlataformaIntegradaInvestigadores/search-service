"""Unitarias de TextVectorizeView y TextProcessingHealthView. Mockea por
completo TextVectorizerService (a nivel del modulo views) para no depender
del singleton ni de sus dependencias pesadas."""

from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APITestCase

VIEWS_MODULE = "apps.text_processing.infrastructure.api.views"


class TestTextVectorizeView(APITestCase):
    def setUp(self):
        self.patcher = patch(f"{VIEWS_MODULE}.TextVectorizerService")
        self.mock_service_cls = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.mock_service = MagicMock()
        self.mock_service.vectorize_text.return_value = {
            "vector": [0.1, 0.2],
            "dimension": 2,
            "original_language": "en",
            "was_translated": False,
            "processed_text": "hello",
            "processing_time": {
                "translation_time": 0,
                "embedding_time": 0.01,
                "total_time": 0.01,
            },
        }
        self.mock_service_cls.return_value = self.mock_service

    def test_vectoriza_texto_correctamente(self):
        response = self.client.post(
            "/api-se/v1/text-processing/vectorize/", {"text": "hello"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["dimension"], 2)
        self.mock_service.vectorize_text.assert_called_once_with(
            text="hello", translate_to_english=True, clean_text=True
        )

    def test_respeta_flags_opcionales(self):
        response = self.client.post(
            "/api-se/v1/text-processing/vectorize/",
            {"text": "hello", "translate_to_english": False, "clean_text": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_service.vectorize_text.assert_called_once_with(
            text="hello", translate_to_english=False, clean_text=False
        )

    def test_sin_campo_text_retorna_400(self):
        response = self.client.post(
            "/api-se/v1/text-processing/vectorize/", {}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_texto_vacio_retorna_400(self):
        response = self.client.post(
            "/api-se/v1/text-processing/vectorize/", {"text": "   "}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_texto_no_string_retorna_400(self):
        response = self.client.post(
            "/api-se/v1/text-processing/vectorize/", {"text": 123}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_error_interno_retorna_500(self):
        self.mock_service.vectorize_text.side_effect = RuntimeError("boom")

        response = self.client.post(
            "/api-se/v1/text-processing/vectorize/", {"text": "hello"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)


class TestTextProcessingHealthView(APITestCase):
    def setUp(self):
        self.patcher = patch(f"{VIEWS_MODULE}.TextVectorizerService")
        self.mock_service_cls = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_healthy_cuando_el_servicio_responde(self):
        mock_service = MagicMock()
        mock_service.vectorize_text.return_value = {"dimension": 768}
        self.mock_service_cls.return_value = mock_service

        response = self.client.get("/api-se/v1/text-processing/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")
        self.assertEqual(response.data["model_dimension"], 768)

    def test_unhealthy_cuando_el_servicio_falla(self):
        self.mock_service_cls.side_effect = RuntimeError("modelo no disponible")

        response = self.client.get("/api-se/v1/text-processing/health/")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "unhealthy")
