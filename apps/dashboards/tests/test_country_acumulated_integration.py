import pytest
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.dashboards.domain.entities.country_acumulated import CountryAcumulated


@pytest.mark.integration
class CountryAcumulatedEndpointIntegrationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        CountryAcumulated.drop_collection()
        CountryAcumulated.objects.create(
            year=2023,
            total_authors=100,
            total_articles=50,
            total_affiliations=20,
            total_topics=30,
        )

    def tearDown(self):
        CountryAcumulated.drop_collection()

    def test_get_acumulated_returns_stored_document(self):
        response = self.client.get(
            "/api-se/v1/dashboard/country/get_acumulated/", {"year": 2023}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["author"], 100)
        self.assertEqual(response.data["article"], 50)
        self.assertEqual(response.data["affiliation"], 20)
        self.assertEqual(response.data["topic"], 30)

    def test_get_acumulated_for_missing_year_returns_500_with_error(self):
        response = self.client.get(
            "/api-se/v1/dashboard/country/get_acumulated/", {"year": 1999}
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
