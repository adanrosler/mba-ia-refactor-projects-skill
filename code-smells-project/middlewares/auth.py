import hmac
from functools import wraps

from flask import current_app, request

from errors import ForbiddenError, UnauthorizedError


def _check_admin_token():
    token = current_app.config.get("ADMIN_TOKEN")
    if not token:
        return  # modo compatível: sem ADMIN_TOKEN configurado, a rota continua aberta
    sent = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if not hmac.compare_digest(sent, token):
        raise UnauthorizedError("Não autorizado")


def admin_token_required(view):
    """Exige `Authorization: Bearer <ADMIN_TOKEN>` quando ADMIN_TOKEN estiver definido."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        _check_admin_token()
        return view(*args, **kwargs)

    return wrapper


def admin_tools_required(view):
    """Rotas destrutivas: desligadas por padrão (ENABLE_ADMIN_ENDPOINTS) e protegidas por token."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_app.config.get("ENABLE_ADMIN_ENDPOINTS"):
            raise ForbiddenError("Endpoint administrativo desabilitado")
        _check_admin_token()
        return view(*args, **kwargs)

    return wrapper
