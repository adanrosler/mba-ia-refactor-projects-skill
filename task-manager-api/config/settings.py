"""Configuração da aplicação lida de variáveis de ambiente (com defaults seguros)."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _origins(value):
    if not value or value.strip() == '*':
        return '*'
    return [origin.strip() for origin in value.split(',') if origin.strip()]


class Settings:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SECRET_KEY_IS_EPHEMERAL = not os.environ.get('SECRET_KEY')

    DEBUG = _bool(os.environ.get('APP_DEBUG'))
    HOST = os.environ.get('HOST', '127.0.0.1')
    PORT = int(os.environ.get('PORT', '5000'))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CORS_ORIGINS = _origins(os.environ.get('CORS_ORIGINS'))

    AUTH_REQUIRED = _bool(os.environ.get('AUTH_REQUIRED'))
    AUTH_TOKEN_MAX_AGE = int(os.environ.get('AUTH_TOKEN_MAX_AGE', '86400'))

    SMTP_HOST = os.environ.get('SMTP_HOST')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

    DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', '20'))
    MAX_PAGE_SIZE = int(os.environ.get('MAX_PAGE_SIZE', '100'))
