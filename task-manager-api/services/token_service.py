from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class TokenService:
    """Emite e valida tokens assinados (HMAC) com expiração. Configurado no composition root."""

    def __init__(self, secret_key, max_age_seconds):
        self._serializer = URLSafeTimedSerializer(secret_key, salt='auth-token')
        self._max_age = max_age_seconds

    def issue(self, user_id):
        return self._serializer.dumps({'uid': user_id})

    def verify(self, token):
        """Devolve o user_id do token, ou None se ausente, adulterado ou expirado."""
        if not token:
            return None
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except (BadSignature, SignatureExpired):
            return None
        user_id = payload.get('uid') if isinstance(payload, dict) else None
        return user_id if isinstance(user_id, int) else None
