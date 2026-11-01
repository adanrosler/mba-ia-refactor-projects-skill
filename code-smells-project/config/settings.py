import os
import secrets

APP_VERSION = "1.0.0"


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    SECRET_KEY_FROM_ENV = "SECRET_KEY" in os.environ
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool(os.environ.get("DEBUG"), default=False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    APP_ENV = os.environ.get("APP_ENV", "producao")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    # Autorização opcional para rotas administrativas/sensíveis (Authorization: Bearer <token>)
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN") or None
    # /admin/query e /admin/reset-db ficam desligados a menos que explicitamente habilitados
    ENABLE_ADMIN_ENDPOINTS = _bool(os.environ.get("ENABLE_ADMIN_ENDPOINTS"), default=False)
