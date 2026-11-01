"""Composition root: cria a aplicação, injeta dependências e registra rotas/middlewares."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.auth import AuthMiddleware
from middlewares.error_handler import register_error_handlers
from routes.category_routes import build_category_routes
from routes.report_routes import build_report_routes
from routes.system_routes import build_system_routes
from routes.task_routes import build_task_routes
from routes.user_routes import build_user_routes
from services.notification_service import NotificationService
from services.token_service import TokenService

logger = logging.getLogger(__name__)


def _warn_insecure_defaults(settings):
    if settings.SECRET_KEY_IS_EPHEMERAL:
        logger.warning('SECRET_KEY não definida; usando chave aleatória (tokens não sobrevivem a restarts)')
    if not settings.AUTH_REQUIRED:
        logger.warning('AUTH_REQUIRED desativado: rotas sensíveis respondem sem autenticação')


def create_app(settings=Settings):
    logging.basicConfig(level=settings.LOG_LEVEL, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)
    _warn_insecure_defaults(settings)

    token_service = TokenService(settings.SECRET_KEY, settings.AUTH_TOKEN_MAX_AGE)
    notifier = NotificationService(settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER, settings.SMTP_PASSWORD)
    auth = AuthMiddleware(token_service, enabled=settings.AUTH_REQUIRED)

    app.register_blueprint(build_system_routes())
    app.register_blueprint(build_task_routes(TaskController(notifier), auth))
    app.register_blueprint(build_user_routes(UserController(token_service, settings.AUTH_REQUIRED), auth))
    app.register_blueprint(build_report_routes(ReportController(), auth))
    app.register_blueprint(build_category_routes(CategoryController(), auth))
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
