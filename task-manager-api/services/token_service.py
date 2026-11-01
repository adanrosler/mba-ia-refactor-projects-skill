from itsdangerous import BadSignature, URLSafeTimedSerializer

TOKEN_SALT = 'auth-token'


class TokenService:
    """Emite e valida tokens assinados (itsdangerous) com expiração."""

    def __init__(self, secret_key, max_age):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=TOKEN_SALT)
        self._max_age = max_age

    def issue(self, user_id):
        return self._serializer.dumps({'uid': user_id})

    def verify(self, token):
        """Retorna o id do usuário do token ou None se inválido/expirado."""
        if not token:
            return None
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except BadSignature:
            return None
        return payload.get('uid') if isinstance(payload, dict) else None
