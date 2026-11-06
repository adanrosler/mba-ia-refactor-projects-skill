"""Autenticação administrativa por credencial estática (fail-closed)."""
import hmac
from functools import wraps

from flask import current_app, request

from errors import UnauthorizedError

BEARER_PREFIX = "Bearer "


def _bearer_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith(BEARER_PREFIX):
        return ""
    return header[len(BEARER_PREFIX):].strip()


def require_admin(view):
    """Exige `Authorization: Bearer <ADMIN_TOKEN>`.

    Nega com 401 quando o header falta, não confere ou quando ADMIN_TOKEN não está
    configurado no ambiente — nunca libera acesso anônimo.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        sent = _bearer_token()
        if not expected or not sent or not hmac.compare_digest(sent.encode(), expected.encode()):
            raise UnauthorizedError("Não autorizado")
        return view(*args, **kwargs)

    return wrapper
