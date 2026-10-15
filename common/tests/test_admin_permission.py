"""Unitarias de IsCentinelaAdmin: la permission que gatea endpoints de admin
(repoblado del datalake, ETL) detras de ADMIN_CENTINELA/PASSWORD_CENTINELA."""

import base64
import os
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from common.admin_permission import IsCentinelaAdmin


def _basic_auth(username: str, password: str) -> str:
    raw = f"{username}:{password}".encode()
    return "Basic " + base64.b64encode(raw).decode("ascii")


class TestIsCentinelaAdmin(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsCentinelaAdmin()

    @patch.dict(
        os.environ, {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"}
    )
    def test_permite_con_credenciales_correctas(self):
        request = self.factory.post(
            "/populate", HTTP_AUTHORIZATION=_basic_auth("admin", "secret")
        )
        self.assertTrue(self.permission.has_permission(request, None))

    @patch.dict(
        os.environ, {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"}
    )
    def test_rechaza_sin_header_de_autorizacion(self):
        request = self.factory.post("/populate")
        self.assertFalse(self.permission.has_permission(request, None))

    @patch.dict(
        os.environ, {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"}
    )
    def test_rechaza_password_incorrecta(self):
        request = self.factory.post(
            "/populate", HTTP_AUTHORIZATION=_basic_auth("admin", "wrong")
        )
        self.assertFalse(self.permission.has_permission(request, None))

    @patch.dict(
        os.environ, {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"}
    )
    def test_rechaza_username_incorrecto(self):
        request = self.factory.post(
            "/populate", HTTP_AUTHORIZATION=_basic_auth("someone_else", "secret")
        )
        self.assertFalse(self.permission.has_permission(request, None))

    @patch.dict(
        os.environ, {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"}
    )
    def test_rechaza_esquema_distinto_de_basic(self):
        request = self.factory.post("/populate", HTTP_AUTHORIZATION="Bearer sometoken")
        self.assertFalse(self.permission.has_permission(request, None))

    @patch.dict(
        os.environ, {"ADMIN_CENTINELA": "admin", "PASSWORD_CENTINELA": "secret"}
    )
    def test_rechaza_base64_invalido(self):
        request = self.factory.post("/populate", HTTP_AUTHORIZATION="Basic ###")
        self.assertFalse(self.permission.has_permission(request, None))

    @patch.dict(os.environ, {}, clear=True)
    def test_rechaza_todo_si_las_variables_de_entorno_no_estan_configuradas(self):
        request = self.factory.post(
            "/populate", HTTP_AUTHORIZATION=_basic_auth("admin", "secret")
        )
        self.assertFalse(self.permission.has_permission(request, None))

    def test_mensaje_de_error_es_informativo(self):
        self.assertEqual(self.permission.message, "Admin credentials required.")
