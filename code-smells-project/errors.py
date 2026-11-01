class AppError(Exception):
    """Erro de domínio convertido em JSON pelo middleware de erros."""

    status = 400

    def __init__(self, message, status=None, payload=None):
        super().__init__(message)
        self.message = message
        self.payload = payload or {}
        if status:
            self.status = status


class ValidationError(AppError):
    status = 400


class NotFoundError(AppError):
    status = 404


class UnauthorizedError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403
