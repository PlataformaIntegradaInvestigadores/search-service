from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from common.admin_permission import issue_admin_token

CREDENTIALS = {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"}


class InternalValidationTests(SimpleTestCase):
    path = "/internal/auth/validate-admin-token/"

    def test_internal_route_accepts_only_a_current_admin_token(self):
        client = APIClient()
        with patch.dict("os.environ", CREDENTIALS):
            token = issue_admin_token()
            for headers, status in (
                ({}, 403),
                ({"HTTP_AUTHORIZATION": "Basic YWRtaW46c2VjcmV0"}, 403),
                ({"HTTP_AUTHORIZATION": "Bearer synthetic-user-token"}, 403),
                ({"HTTP_X_ADMIN_TOKEN": "invalid"}, 403),
                ({"HTTP_X_ADMIN_TOKEN": token}, 204),
            ):
                with self.subTest(status=status):
                    response = client.get(self.path, **headers)
                    self.assertEqual(response.status_code, status)
                    self.assertEqual(response.content, b"")
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
            with patch("django.core.signing.time.time", return_value=10**10):
                self.assertEqual(
                    client.get(self.path, HTTP_X_ADMIN_TOKEN=token).status_code, 403
                )
            with patch.dict("os.environ", {"PASSWORD_CENTINELA": "rotated"}):
                self.assertEqual(
                    client.get(self.path, HTTP_X_ADMIN_TOKEN=token).status_code, 403
                )
            self.assertEqual(
                client.post(self.path, HTTP_X_ADMIN_TOKEN=token).status_code, 405
            )
