"""Unitarias de LoginView/LogoutView y LoginRequestSerializer."""

from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.infrastructure.api.v1.serializers.login_request_serializer import (
    LoginRequestSerializer,
)

LOGIN_URL = "/api-se/v1/auth/login/"
LOGOUT_URL = "/api-se/v1/auth/logout/"


class TestLoginRequestSerializer(APITestCase):
    def test_campos_requeridos(self):
        serializer = LoginRequestSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)
        self.assertIn("password", serializer.errors)

    def test_datos_validos(self):
        serializer = LoginRequestSerializer(
            data={"username": "admin", "password": "secret"}
        )
        self.assertTrue(serializer.is_valid())


class TestLoginView(APITestCase):
    @patch.dict(
        "os.environ",
        {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"},
    )
    def test_credenciales_validas_retorna_200(self):
        response = self.client.post(
            LOGIN_URL, {"username": "admin", "password": "secret"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Login Succesfull")

    @patch.dict(
        "os.environ",
        {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"},
    )
    def test_credenciales_invalidas_retorna_400(self):
        response = self.client.post(
            LOGIN_URL, {"username": "admin", "password": "wrong"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid Credentials")

    def test_sin_credenciales_configuradas_retorna_400(self):
        response = self.client.post(LOGIN_URL, {"username": "x", "password": "y"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestLogoutView(APITestCase):
    def test_logout_retorna_200(self):
        response = self.client.post(LOGOUT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Logout exitoso")
