from rest_framework import status
from rest_framework.test import APITestCase


class OpenAPISchemaTests(APITestCase):
    def test_schema_uses_gateway_prefix(self):
        response = self.client.get("/api-se/schema/", {"format": "json"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema = response.json()
        self.assertEqual(
            schema["servers"], [{"url": "/api/search", "description": "Gateway"}]
        )
        self.assertTrue(
            all(not path.startswith("/api-se") for path in schema["paths"])
        )
