import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Converte todos os erros em JSON `{'error': <mensagem>}` mantendo os status originais."""

    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({'error': err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
