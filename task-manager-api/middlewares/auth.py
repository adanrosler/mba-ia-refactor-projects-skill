from functools import wraps

from flask import g, request

from models.user import User
from utils.errors import ForbiddenError, UnauthorizedError

BEARER_PREFIX = 'Bearer '


class AuthMiddleware:
    """Autenticação por token assinado, ativável por configuração (AUTH_REQUIRED).

    Desativada, as rotas respondem como antes (modo compatível) — um warning é
    logado no boot pelo composition root.
    """

    def __init__(self, token_service, enabled=False):
        self.token_service = token_service
        self.enabled = enabled

    def _user_from_request(self):
        header = request.headers.get('Authorization', '')
        token = header[len(BEARER_PREFIX):] if header.startswith(BEARER_PREFIX) else None
        user_id = self.token_service.verify(token)
        user = User.get(user_id) if user_id is not None else None
        return user if user and user.active else None

    @staticmethod
    def current_user():
        return g.get('current_user')

    def required(self, roles=None):
        def decorator(view):
            @wraps(view)
            def wrapper(*args, **kwargs):
                if self.enabled:
                    user = self._user_from_request()
                    if not user:
                        raise UnauthorizedError('Não autorizado')
                    if roles and user.role not in roles:
                        raise ForbiddenError('Permissão negada')
                    g.current_user = user
                return view(*args, **kwargs)
            return wrapper
        return decorator

    def optional(self, view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            g.current_user = self._user_from_request() if self.enabled else None
            return view(*args, **kwargs)
        return wrapper
