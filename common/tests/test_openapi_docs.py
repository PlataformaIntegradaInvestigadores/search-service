"""El Swagger de search-service esta completo, agrupado y en espanol.

La documentacion vive en ``config/openapi_docs.py``. Estas pruebas fallan si se agrega
una ruta sin documentar, si la tabla apunta a una ruta que ya no existe o si el
documento deja de ser coherente.
"""

import re
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from drf_spectacular.generators import SchemaGenerator

from config.openapi_docs import OPERATIONS, TAGS

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
SCHEMA_REF = re.compile(r"#/components/schemas/([A-Za-z0-9_]+)")
ADMIN_OPERATIONS = {("post", "/v1/dashboard/populate"), ("delete", "/v1/articles/{id}/")}


class OpenAPIDocumentationTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # El generador introspecciona los serializers de mongoengine, que piden la
        # coleccion; no hace falta una base real para generar el documento.
        with patch(
            "mongoengine.document.Document._get_collection",
            classmethod(lambda klass: MagicMock()),
        ):
            cls.schema = SchemaGenerator().get_schema(request=None, public=True)

    def operations(self):
        for path, item in self.schema["paths"].items():
            for method, operation in item.items():
                if method in HTTP_METHODS:
                    yield path, method, operation

    def test_every_operation_has_summary_description_and_one_declared_tag(self):
        declared = {tag["name"] for tag in TAGS}
        for path, method, operation in self.operations():
            label = f"{method.upper()} {path}"
            self.assertTrue(operation.get("summary"), f"{label} sin resumen")
            self.assertTrue(operation.get("description"), f"{label} sin descripción")
            self.assertEqual(len(operation.get("tags", [])), 1, label)
            self.assertIn(operation["tags"][0], declared, label)

    def test_tags_are_declared_in_order_with_a_description(self):
        names = [tag["name"] for tag in self.schema["tags"]]
        self.assertEqual(names, [tag["name"] for tag in TAGS])
        self.assertTrue(all(tag["description"] for tag in self.schema["tags"]))
        used = {operation["tags"][0] for _, _, operation in self.operations()}
        self.assertEqual(used, set(names))

    def test_every_route_in_the_table_exists_and_every_route_is_documented(self):
        published = {
            (method, path) for path, method, _ in self.operations()
        }
        for method, key in OPERATIONS:
            self.assertIn((method.lower(), "/v1" + key), published, key)
        documented = {(m.lower(), "/v1" + k) for (m, k) in OPERATIONS}
        self.assertEqual(published - documented, set())

    def test_inherited_crud_routes_of_the_dashboard_are_hidden(self):
        crud = re.compile(
            r"^/v1/dashboard/(affiliation|author|country|province)/(\{[^/]*\}/)?$"
        )
        for path in self.schema["paths"]:
            self.assertIsNone(crud.match(path), path)

    def test_dashboards_do_not_advertise_pagination(self):
        for path, method, operation in self.operations():
            if path.startswith("/v1/dashboard/"):
                names = [p["name"] for p in operation.get("parameters", [])]
                self.assertNotIn("page", names, f"{method.upper()} {path}")
        for name in self.schema["components"]["schemas"]:
            self.assertFalse(name.startswith(("Paginated", "Patched")), name)

    def test_only_admin_operations_ask_for_credentials(self):
        for path, method, operation in self.operations():
            expected = [{"basicAuth": []}] if (method, path) in ADMIN_OPERATIONS else []
            self.assertEqual(operation["security"], expected, f"{method} {path}")
        self.assertEqual(
            list(self.schema["components"]["securitySchemes"]), ["basicAuth"]
        )

    def test_every_response_is_described_and_success_has_a_schema(self):
        for path, method, operation in self.operations():
            for code, response in operation["responses"].items():
                label = f"{method.upper()} {path} {code}"
                self.assertTrue(response.get("description"), label)
                if code.startswith("2") and code != "204":
                    schema = response["content"]["application/json"]["schema"]
                    self.assertTrue(schema, label)

    def test_every_reference_resolves(self):
        import json

        schemas = self.schema["components"]["schemas"]
        text = json.dumps(self.schema, default=str)
        for name in set(SCHEMA_REF.findall(text)):
            self.assertIn(name, schemas, name)

    def test_unused_schemas_are_removed(self):
        import json

        schemas = self.schema["components"]["schemas"]
        text = json.dumps(self.schema["paths"], default=str)
        referenced = set(SCHEMA_REF.findall(text))
        pending = list(referenced)
        while pending:
            name = pending.pop()
            for inner in SCHEMA_REF.findall(json.dumps(schemas[name], default=str)):
                if inner not in referenced:
                    referenced.add(inner)
                    pending.append(inner)
        self.assertEqual(set(schemas) - referenced, set())

    def test_every_schema_property_has_a_description(self):
        for name, definition in self.schema["components"]["schemas"].items():
            for prop, spec in definition.get("properties", {}).items():
                described = spec.get("description") or any(
                    "description" in part for part in spec.get("allOf", [])
                )
                self.assertTrue(described, f"{name}.{prop} sin descripción")

    def test_path_parameters_are_described(self):
        for path, method, operation in self.operations():
            for parameter in operation.get("parameters", []):
                label = f"{method.upper()} {path} {parameter['name']}"
                self.assertTrue(parameter.get("description"), label)

    def test_info_is_in_spanish_and_lists_the_groups(self):
        info = self.schema["info"]
        self.assertIn("corpus científico", info["title"])
        self.assertIn("no paginan", info["description"])

    def test_post_operations_that_read_a_body_document_it(self):
        with_body = {
            "/v1/llm-search/semantic-search/",
            "/v1/llm-search/generate-qa/",
            "/v1/text-processing/vectorize/",
            "/v1/auth/login/",
            "/v1/articles/most-relevant-articles-by-topic/",
            "/v1/authors/most_relevant_authors/",
        }
        for path, method, operation in self.operations():
            if method == "post" and path in with_body:
                body = operation["requestBody"]["content"]["application/json"]
                self.assertTrue(body["schema"], path)
                self.assertTrue(operation["requestBody"]["required"], path)
