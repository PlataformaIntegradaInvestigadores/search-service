import base64
import binascii
import hashlib
import hmac
import os

from django.core import signing
from rest_framework.permissions import BasePermission

ADMIN_TOKEN_HEADER = "HTTP_X_ADMIN_TOKEN"
ADMIN_TOKEN_SALT = "centinela.admin-token"
ADMIN_TOKEN_DEFAULT_MAX_AGE = 8 * 60 * 60


def admin_token_max_age() -> int:
    raw = os.environ.get("ADMIN_TOKEN_MAX_AGE_SECONDS", "")
    return int(raw) if raw.isdigit() and int(raw) > 0 else ADMIN_TOKEN_DEFAULT_MAX_AGE


def _credentials_fingerprint() -> str | None:
    """Huella de las credenciales vigentes: al rotarlas, los tokens emitidos dejan
    de valer aunque no hayan vencido."""
    admin = os.environ.get("ADMIN_CENTINELA")
    password = os.environ.get("PASSWORD_CENTINELA")
    if not admin or not password:
        return None
    return hashlib.sha256(f"{admin}:{password}".encode()).hexdigest()[:16]


def issue_admin_token() -> str:
    """Token firmado (con SECRET_KEY) que el panel manda en ``X-Admin-Token``."""
    return signing.dumps(
        {"role": "admin", "fp": _credentials_fingerprint()}, salt=ADMIN_TOKEN_SALT
    )


def is_valid_admin_token(token: str) -> bool:
    expected = _credentials_fingerprint()
    if not token or expected is None:
        return False
    try:
        data = signing.loads(
            token, salt=ADMIN_TOKEN_SALT, max_age=admin_token_max_age()
        )
    except signing.BadSignature:  # incluye SignatureExpired
        return False
    return data.get("role") == "admin" and hmac.compare_digest(
        str(data.get("fp")), expected
    )


class IsCentinelaAdmin(BasePermission):
    """Gates admin-only endpoints (datalake repopulation, ETL triggers, ...).

    Acepta cualquiera de dos formas de demostrar que se es administrador:

    * ``X-Admin-Token``: token firmado que entrega ``LoginView`` al validar el par
      ADMIN_CENTINELA/PASSWORD_CENTINELA. Es lo que usa el panel de administracion,
      que asi no guarda la contrasena y no choca con el JWT del usuario en
      ``Authorization``.
    * HTTP Basic con ese mismo par, para scripts y herramientas como Postman.

    No se emite sesion ni JWT en este servicio; esto solo evita que los endpoints
    sean alcanzables por cualquiera que conozca la URL publica del gateway.
    """

    message = "Admin credentials required."

    def has_permission(self, request, view) -> bool:
        token = request.META.get(ADMIN_TOKEN_HEADER, "")
        if token and is_valid_admin_token(token):
            return True
        return self._has_valid_basic_credentials(request)

    @staticmethod
    def _has_valid_basic_credentials(request) -> bool:
        admin_centinela = os.environ.get("ADMIN_CENTINELA")
        password_centinela = os.environ.get("PASSWORD_CENTINELA")
        if not admin_centinela or not password_centinela:
            return False

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        scheme, _, credentials = auth_header.partition(" ")
        if scheme.lower() != "basic" or not credentials:
            return False

        try:
            decoded = base64.b64decode(credentials).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return False

        username, _, password = decoded.partition(":")
        return hmac.compare_digest(username, admin_centinela) and hmac.compare_digest(
            password, password_centinela
        )
