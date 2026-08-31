from django.conf import settings
from django.test import SimpleTestCase


class OpenAPISchemaSettingsTests(SimpleTestCase):
    """Generating the full schema needs live Neo4j/Mongo connections (84
    endpoints across mongoengine/neomodel serializers), so this checks the
    trim/server config directly instead of round-tripping through the
    schema HTTP endpoint in a unit test."""

    def test_schema_path_prefix_trims_internal_prefix(self):
        self.assertEqual(settings.SPECTACULAR_SETTINGS["SCHEMA_PATH_PREFIX"], "/api-se")
        self.assertTrue(settings.SPECTACULAR_SETTINGS["SCHEMA_PATH_PREFIX_TRIM"])

    def test_schema_servers_point_to_gateway_prefix(self):
        self.assertEqual(
            settings.SPECTACULAR_SETTINGS["SERVERS"],
            [{"url": "/api/search", "description": "Gateway"}],
        )
