"""Unitarias de ScopusClient.exec_request: headers, rate-limiting, y manejo
de respuestas HTTP (200 vs error)."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.scopus_integration.application.services.scopus_client import ScopusClient


class ScopusClientTests(SimpleTestCase):
    def setUp(self):
        # Evita que el rate-limiter real duerma entre tests.
        ScopusClient._ScopusClient__ts_last_req = 0

    def _mock_session(self, response):
        session = MagicMock()
        session.get.return_value = response
        return session

    def test_respuesta_200_retorna_json_decodificado(self):
        response = MagicMock(status_code=200, text='{"ok": true}')
        client = ScopusClient()

        with patch("requests.Session", return_value=self._mock_session(response)):
            result = client.exec_request("http://x")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(client._status_code, 200)

    def test_respuesta_no_200_lanza_httperror_con_json_decodificado(self):
        response = MagicMock(status_code=400, text='{"error-response": "bad"}')
        client = ScopusClient()

        with patch("requests.Session", return_value=self._mock_session(response)):
            with self.assertRaises(Exception) as ctx:
                client.exec_request("http://x")

        import requests

        self.assertIsInstance(ctx.exception, requests.HTTPError)

    def test_error_de_red_se_envuelve_en_exception_generica(self):
        client = ScopusClient()

        with patch("requests.Session", side_effect=RuntimeError("boom")):
            with self.assertRaises(Exception) as ctx:
                client.exec_request("http://x")

        self.assertIn("Error executing request", str(ctx.exception))

    def test_espera_el_intervalo_minimo_entre_peticiones(self):
        response = MagicMock(status_code=200, text="{}")
        client = ScopusClient()
        ScopusClient._ScopusClient__ts_last_req = __import__("time").time()

        with patch("requests.Session", return_value=self._mock_session(response)):
            with patch("time.sleep") as mock_sleep:
                client.exec_request("http://x")

        mock_sleep.assert_called_once()

    def test_headers_incluyen_tokens_opcionales_si_estan_presentes(self):
        response = MagicMock(status_code=200, text="{}")
        client = ScopusClient()
        client.x_els_auth_token = "auth-tok"
        client.x_els_ins_token = "ins-tok"
        session = self._mock_session(response)

        with patch("requests.Session", return_value=session):
            client.exec_request("http://x")

        headers = session.get.call_args.kwargs["headers"]
        self.assertEqual(headers["X-ELS-Authtoken"], "auth-tok")
        self.assertEqual(headers["X-ELS-Insttoken"], "ins-tok")
