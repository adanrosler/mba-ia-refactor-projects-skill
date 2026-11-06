"""Configuração da aplicação lida de variáveis de ambiente, com defaults seguros."""
import os
import secrets


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _int(value, default):
    try:
        return int(value) if value else default
    except ValueError:
        return default


class Settings:
    # Sem SECRET_KEY no ambiente → chave aleatória por processo (tokens não sobrevivem a restarts).
    SECRET_KEY_FROM_ENV = bool(os.environ.get('SECRET_KEY'))
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    DEBUG = _bool(os.environ.get('APP_DEBUG'), default=False)
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = _int(os.environ.get('PORT'), 5000)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TOKEN_MAX_AGE_SECONDS = _int(os.environ.get('TOKEN_MAX_AGE_SECONDS'), 24 * 60 * 60)

    # SMTP opcional: sem host/usuário/senha o serviço de notificação fica desabilitado.
    SMTP_HOST = os.environ.get('SMTP_HOST')
    SMTP_PORT = _int(os.environ.get('SMTP_PORT'), 587)
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
