"""Token de administracion: emision en LoginView, validacion y endpoints protegidos."""

import base64
import os
from unittest.mock import patch

from django.core import signing
from django.test import SimpleTestCase
from rest_framework.test import APIClient, APIRequestFactory

from common.admin_permission import (
    IsCentinelaAdmin,
    admin_token_max_age,
    is_valid_admin_token,
    issue_admin_token,
)

CREDENTIALS = {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"}
factory = APIRequestFactory()

PROTECTED = [
    ("get", "/api-se/v1/admin/etl/run/"),
    ("post", "/api-se/v1/admin/etl/run/"),
    ("get", "/api-se/v1/admin/logs/"),
    ("post", "/api-se/v1/generate-corpus/"),
    ("post", "/api-se/v1/generate-model/"),
    ("get", "/api-se/v1/scopus-integration/"),
    ("post", "/api-se/v1/information/update/author-information/"),
    ("post", "/api-se/v1/dashboard/populate"),
]


def basic(user, password):
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"HTTP_AUTHORIZATION": f"Basic {token}"}


class AdminTokenTests(SimpleTestCase):
    def test_issued_token_is_valid(self):
        with patch.dict(os.environ, CREDENTIALS):
            self.assertTrue(is_valid_admin_token(issue_admin_token()))

    def test_tampered_token_is_rejected(self):
        with patch.dict(os.environ, CREDENTIALS):
            token = issue_admin_token()
            self.assertFalse(is_valid_admin_token(token[:-2] + "xx"))
            self.assertFalse(is_valid_admin_token("no-es-un-token"))
            self.assertFalse(is_valid_admin_token(""))

    def test_token_from_another_purpose_is_rejected(self):
        with patch.dict(os.environ, CREDENTIALS):
            other = signing.dumps({"role": "admin"}, salt="otro-proposito")
            self.assertFalse(is_valid_admin_token(other))

    def test_token_expires(self):
        with patch.dict(os.environ, {**CREDENTIALS, "ADMIN_TOKEN_MAX_AGE_SECONDS": "60"}):
            token = issue_admin_token()
            self.assertTrue(is_valid_admin_token(token))
            with patch("django.core.signing.time.time", return_value=10**10):
                self.assertFalse(is_valid_admin_token(token))

    def test_rotating_the_credentials_invalidates_issued_tokens(self):
        with patch.dict(os.environ, CREDENTIALS):
            token = issue_admin_token()
        with patch.dict(os.environ, {**CREDENTIALS, "PASSWORD_CENTINELA": "nueva"}):
            self.assertFalse(is_valid_admin_token(token))

    def test_without_configured_credentials_no_token_is_valid(self):
        with patch.dict(os.environ, CREDENTIALS):
            token = issue_admin_token()
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(is_valid_admin_token(token))

    def test_max_age_defaults_to_eight_hours(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(admin_token_max_age(), 8 * 60 * 60)
        with patch.dict(os.environ, {"ADMIN_TOKEN_MAX_AGE_SECONDS": "abc"}):
            self.assertEqual(admin_token_max_age(), 8 * 60 * 60)


class PermissionTests(SimpleTestCase):
    def check(self, **headers):
        request = factory.get("/", **headers)
        return IsCentinelaAdmin().has_permission(request, None)

    def test_accepts_a_valid_token(self):
        with patch.dict(os.environ, CREDENTIALS):
            self.assertTrue(self.check(HTTP_X_ADMIN_TOKEN=issue_admin_token()))

    def test_accepts_basic_credentials(self):
        with patch.dict(os.environ, CREDENTIALS):
            self.assertTrue(self.check(**basic("admin", "secret")))

    def test_rejects_a_bad_token_and_missing_credentials(self):
        with patch.dict(os.environ, CREDENTIALS):
            self.assertFalse(self.check(HTTP_X_ADMIN_TOKEN="basura"))
            self.assertFalse(self.check())
            self.assertFalse(self.check(**basic("admin", "mal")))


class LoginIssuesTokenTests(SimpleTestCase):
    def post(self, **body):
        return APIClient().post("/api-se/v1/auth/login/", body, format="json")

    def test_valid_login_returns_a_usable_token(self):
        with patch.dict(os.environ, CREDENTIALS):
            response = self.post(username="admin", password="secret")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["message"], "Login Succesfull")
            self.assertTrue(is_valid_admin_token(response.data["token"]))
            self.assertEqual(response.data["expires_in"], 8 * 60 * 60)

    def test_invalid_login_returns_no_token(self):
        with patch.dict(os.environ, CREDENTIALS):
            response = self.post(username="admin", password="mal")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("token", response.data)


class ProtectedEndpointsTests(SimpleTestCase):
    def test_every_admin_endpoint_rejects_anonymous_requests(self):
        client = APIClient()
        with patch.dict(os.environ, CREDENTIALS):
            for method, path in PROTECTED:
                response = getattr(client, method)(path)
                self.assertEqual(response.status_code, 403, f"{method} {path}")

    def test_every_admin_endpoint_rejects_a_forged_token(self):
        client = APIClient()
        with patch.dict(os.environ, CREDENTIALS):
            for method, path in PROTECTED:
                response = getattr(client, method)(path, HTTP_X_ADMIN_TOKEN="falso")
                self.assertEqual(response.status_code, 403, f"{method} {path}")

    def test_admin_views_declare_the_permission_and_skip_basic_authentication(self):
        from django.urls import resolve

        for method, path in PROTECTED:
            view = resolve(path).func
            cls = getattr(view, "cls", None) or view.view_class
            self.assertEqual(cls.permission_classes, [IsCentinelaAdmin], path)
            self.assertEqual(cls.authentication_classes, [], path)
