import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from database import db
from utils.errors import AppError

logger = logging.getLogger(__name__)

ERROR_KEY = 'error'


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({ERROR_KEY: err.message}), err.status

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({ERROR_KEY: err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        db.session.rollback()
        logger.exception('Erro não tratado')
        return jsonify({ERROR_KEY: 'Erro interno'}), 500
