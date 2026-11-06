"""Configuração da aplicação lida do ambiente, com defaults seguros."""
import logging
import os
import secrets

logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
DEFAULT_DATABASE_PATH = "loja.db"
DEFAULT_ENVIRONMENT = "producao"


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on", "sim")


def load_settings():
    """Lê as variáveis de ambiente no momento da criação da aplicação."""
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        logger.warning("SECRET_KEY não definida; usando chave aleatória (não persiste entre restarts)")
        secret_key = secrets.token_hex(32)

    admin_token = os.environ.get("ADMIN_TOKEN") or None
    if not admin_token:
        logger.warning(
            "ADMIN_TOKEN não definido; rotas protegidas responderão 401 até a variável ser configurada"
        )

    return {
        "SECRET_KEY": secret_key,
        "DEBUG": _bool(os.environ.get("APP_DEBUG"), default=False),
        "HOST": os.environ.get("HOST", DEFAULT_HOST),
        "PORT": int(os.environ.get("PORT", DEFAULT_PORT)),
        "DATABASE_PATH": os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH),
        "APP_ENV": os.environ.get("APP_ENV", DEFAULT_ENVIRONMENT),
        "ADMIN_TOKEN": admin_token,
        "ENABLE_ADMIN_ENDPOINTS": _bool(os.environ.get("ENABLE_ADMIN_ENDPOINTS"), default=False),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO").upper(),
    }
