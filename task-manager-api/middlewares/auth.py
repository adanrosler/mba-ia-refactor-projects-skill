"""Autenticação por token assinado (emitido no /login). Sempre ligada, fail-closed."""
from functools import wraps

from flask import current_app, g, request

from models.user import User
from utils.errors import ForbiddenError, UnauthorizedError


def _bearer_token():
    scheme, _, token = request.headers.get('Authorization', '').partition(' ')
    return token.strip() if scheme == 'Bearer' and token.strip() else None


def current_user_or_none():
    """Usuário ativo dono de um token válido, ou None (sem token, token inválido/expirado)."""
    token_service = current_app.extensions['token_service']
    user_id = token_service.verify(_bearer_token())
    if user_id is None:
        return None
    user = User.find(user_id)
    return user if user is not None and user.active else None


def require_auth(roles=None):
    """Exige token válido (401) e, se `roles` for informado, um desses papéis (403)."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user_or_none()
            if user is None:
                raise UnauthorizedError('Não autorizado')
            if roles and user.role not in roles:
                raise ForbiddenError('Permissão negada')
            g.current_user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator
