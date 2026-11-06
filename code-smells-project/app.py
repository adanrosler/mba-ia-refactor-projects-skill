"""Composition root: cria a aplicação, injeta dependências e sobe o servidor."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import APP_VERSION, load_settings
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from controllers.relatorio_controller import RelatorioController
from controllers.sistema_controller import SistemaController
from controllers.usuario_controller import UsuarioController
from middlewares.error_handler import register_error_handlers
from models import database, pedido_model, produto_model, relatorio_model, sistema_model, usuario_model
from models.seed import seed_if_empty
from services.notification_service import NotificationService
from views.pedido_routes import build_pedido_blueprint
from views.produto_routes import build_produto_blueprint
from views.relatorio_routes import build_relatorio_blueprint
from views.root_routes import build_root_blueprint
from views.sistema_routes import build_sistema_blueprint
from views.usuario_routes import build_usuario_blueprint

logger = logging.getLogger(__name__)


def create_app(overrides=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    if overrides:
        settings.update(overrides)
    logging.getLogger().setLevel(settings["LOG_LEVEL"])

    app = Flask(__name__)
    app.config.from_mapping(settings)
    CORS(app)

    database.init_app(app, seed=seed_if_empty)
    register_error_handlers(app)

    notificador = NotificationService()
    app.register_blueprint(build_root_blueprint(APP_VERSION))
    app.register_blueprint(build_produto_blueprint(ProdutoController(produto_model)))
    app.register_blueprint(build_usuario_blueprint(UsuarioController(usuario_model)))
    app.register_blueprint(build_pedido_blueprint(PedidoController(pedido_model, notificador)))
    app.register_blueprint(build_relatorio_blueprint(RelatorioController(relatorio_model)))
    app.register_blueprint(build_sistema_blueprint(SistemaController(
        sistema_model,
        versao=APP_VERSION,
        ambiente=settings["APP_ENV"],
        debug=settings["DEBUG"],
        admin_habilitado=settings["ENABLE_ADMIN_ENDPOINTS"],
    )))
    return app


if __name__ == "__main__":
    application = create_app()
    host, port = application.config["HOST"], application.config["PORT"]
    logger.info("Servidor iniciado em http://%s:%s", host, port)
    application.run(host=host, port=port, debug=application.config["DEBUG"])
