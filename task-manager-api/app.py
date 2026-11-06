"""Composition root: cria a aplicação, injeta dependências e registra rotas/middlewares."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.system_controller import SystemController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import create_category_blueprint
from routes.report_routes import create_report_blueprint
from routes.system_routes import create_system_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint
from services.notification_service import NotificationService
from services.token_service import TokenService

import models  # noqa: F401  (registra as entidades antes do create_all)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)


def create_app(settings=Settings):
    app = Flask(__name__)
    app.config.from_object(settings)

    if not settings.SECRET_KEY_FROM_ENV:
        logger.warning('SECRET_KEY não definida; usando chave aleatória. Tokens emitidos não '
                       'sobrevivem a restarts e rotas protegidas exigem novo login.')

    CORS(app)
    db.init_app(app)

    token_service = TokenService(settings.SECRET_KEY, settings.TOKEN_MAX_AGE_SECONDS)
    notifier = NotificationService(host=settings.SMTP_HOST, port=settings.SMTP_PORT,
                                   user=settings.SMTP_USER, password=settings.SMTP_PASSWORD)
    app.extensions['token_service'] = token_service

    register_error_handlers(app)
    app.register_blueprint(create_system_blueprint(SystemController()))
    app.register_blueprint(create_task_blueprint(TaskController(notifier)))
    app.register_blueprint(create_user_blueprint(UserController(token_service)))
    app.register_blueprint(create_category_blueprint(CategoryController()))
    app.register_blueprint(create_report_blueprint(ReportController()))

    with app.app_context():
        db.create_all()
    return app


# `seed.py` e `flask --app app` importam `app` deste módulo.
app = create_app()

if __name__ == '__main__':
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
