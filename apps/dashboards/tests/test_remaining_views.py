"""Unitarias de las vistas delgadas que quedaban sin cubrir: AuthorViews,
ProvinceViews, PopulateView y las 4 vistas de fairness (sirven un JSON
pre-calculado desde disco, no recalculan nada)."""

from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.dashboards.domain.entities.author_topics import AuthorTopics
from apps.dashboards.domain.entities.author_year import AuthorYear
from apps.dashboards.domain.entities.province import Province
from apps.dashboards.domain.entities.province_acumulated import ProvinceAcumulated
from apps.dashboards.domain.entities.province_year import ProvinceYear
from apps.dashboards.infrastructure.api.v1.views import fairness_views

AUTHOR_BASE = "/api-se/v1/dashboard/author/"
PROVINCE_BASE = "/api-se/v1/dashboard/province/"
POPULATE_URL = "/api-se/v1/dashboard/populate"
FAIRNESS_BASE = "/api-se/v1/dashboard/fairness/"


class AuthorViewsTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_author_years_retorna_datos_ordenados(self):
        AuthorYear.objects.create(scopus_id=1, year=2020, total_articles=3)
        AuthorYear.objects.create(scopus_id=1, year=1999, total_articles=1)

        response = self.client.get(f"{AUTHOR_BASE}get_author_years/", {"scopus_id": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["year"], 2020)

    def test_get_author_years_error_retorna_500(self):
        with patch(
            "apps.dashboards.infrastructure.api.v1.views.author_views.AuthorYear.objects",
            side_effect=Exception("boom"),
        ):
            response = self.client.get(
                f"{AUTHOR_BASE}get_author_years/", {"scopus_id": 1}
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_get_topics_retorna_texto_y_tamano(self):
        AuthorTopics.objects.create(scopus_id=2, topic_name="IA", total_articles=5)
        AuthorTopics.objects.create(scopus_id=2, topic_name="", total_articles=9)

        response = self.client.get(f"{AUTHOR_BASE}get_topics/", {"scopus_id": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"text": "IA", "size": 5}])

    def test_get_topics_error_retorna_500(self):
        with patch(
            "apps.dashboards.infrastructure.api.v1.views.author_views.AuthorTopics.objects",
            side_effect=Exception("boom"),
        ):
            response = self.client.get(f"{AUTHOR_BASE}get_topics/", {"scopus_id": 2})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProvinceViewsTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_provinces_retorna_datos(self):
        Province.objects.create(province_name="Pichincha")
        Province.objects.create(province_name="Pendiente")

        response = self.client.get(f"{PROVINCE_BASE}get_provinces/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_provinces_error_retorna_500(self):
        with patch(
            "apps.dashboards.application.services.province_service."
            "Province.objects",
            side_effect=Exception("boom"),
        ):
            response = self.client.get(f"{PROVINCE_BASE}get_provinces/")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_get_provinces_year_retorna_datos(self):
        ProvinceYear.objects.create(
            province_name="Pichincha", year=2020, total_articles=4
        )

        response = self.client.get(f"{PROVINCE_BASE}get_provinces_year/", {"year": 2020})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_provinces_year_error_retorna_500(self):
        with patch(
            "apps.dashboards.application.services.province_service."
            "ProvinceYear.objects",
            side_effect=Exception("boom"),
        ):
            response = self.client.get(
                f"{PROVINCE_BASE}get_provinces_year/", {"year": 2020}
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_get_provinces_acumulated_retorna_datos(self):
        ProvinceAcumulated.objects.create(
            province_name="Pichincha", year=2020, total_articles=4
        )

        response = self.client.get(
            f"{PROVINCE_BASE}get_provinces_acumulated/", {"year": 2020}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_provinces_acumulated_error_retorna_500(self):
        with patch(
            "apps.dashboards.application.services.province_service."
            "ProvinceAcumulated.objects",
            side_effect=Exception("boom"),
        ):
            response = self.client.get(
                f"{PROVINCE_BASE}get_provinces_acumulated/", {"year": 2020}
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class PopulateViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_populate_ok(self):
        with patch(
            "apps.dashboards.infrastructure.api.v1.views.populate_view."
            "PopulateUseCase.execute",
            return_value=None,
        ):
            response = self.client.post(POPULATE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Analytics DB populated")

    def test_post_populate_error_retorna_500(self):
        with patch(
            "apps.dashboards.infrastructure.api.v1.views.populate_view."
            "PopulateUseCase.execute",
            side_effect=Exception("boom"),
        ):
            response = self.client.post(POPULATE_URL)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class FairnessViewsTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        fairness_views._load_fairness_data.cache_clear()

    def tearDown(self):
        fairness_views._load_fairness_data.cache_clear()

    def test_summary_devuelve_json_completo(self):
        response = self.client.get(f"{FAIRNESS_BASE}summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_baseline_devuelve_solo_su_seccion(self):
        response = self.client.get(f"{FAIRNESS_BASE}baseline/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mitigation_devuelve_solo_su_seccion(self):
        response = self.client.get(f"{FAIRNESS_BASE}mitigation/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sensitivity_devuelve_solo_su_seccion(self):
        response = self.client.get(f"{FAIRNESS_BASE}sensitivity/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_datos_no_disponibles_retorna_404(self):
        with patch.object(
            fairness_views,
            "_load_fairness_data",
            side_effect=FileNotFoundError,
        ):
            response = self.client.get(f"{FAIRNESS_BASE}summary/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])
