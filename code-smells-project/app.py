import logging

from flask import Flask
from flask_cors import CORS

from config.settings import APP_VERSION, Settings
from controllers.admin_controller import AdminController
from controllers.health_controller import HealthController
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from controllers.relatorio_controller import RelatorioController
from controllers.usuario_controller import UsuarioController
from middlewares.error_handler import register_error_handlers
from models import database
from models.admin_model import AdminModel
from models.pedido_model import PedidoModel
from models.produto_model import ProdutoModel
from models.relatorio_model import RelatorioModel
from models.seed import seed_if_empty
from models.usuario_model import UsuarioModel, migrar_senhas_texto_puro
from services.notification_service import NotificationService
from views.admin_routes import build_admin_routes
from views.health_routes import build_health_routes
from views.pedido_routes import build_pedido_routes
from views.produto_routes import build_produto_routes
from views.relatorio_routes import build_relatorio_routes
from views.root_routes import build_root_routes
from views.usuario_routes import build_usuario_routes

logger = logging.getLogger(__name__)


def _warn_insecure_defaults(config):
    if not Settings.SECRET_KEY_FROM_ENV:
        logger.warning("SECRET_KEY não definida; usando chave aleatória (não persiste entre restarts)")
    if not config["ADMIN_TOKEN"]:
        logger.warning("ADMIN_TOKEN não definido; rotas administrativas/sensíveis respondem sem autenticação")
    if config["ENABLE_ADMIN_ENDPOINTS"]:
        logger.warning("ENABLE_ADMIN_ENDPOINTS ativo: /admin/query e /admin/reset-db habilitados")


def create_app(settings=Settings):
    logging.basicConfig(level=settings.LOG_LEVEL,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(settings)
    app.config["APP_VERSION"] = APP_VERSION
    CORS(app)

    database.init_app(app, on_init=(seed_if_empty, migrar_senhas_texto_puro))

    get_db = database.get_db
    produtos = ProdutoModel(get_db)
    usuarios = UsuarioModel(get_db)
    pedidos = PedidoModel(get_db)

    app.register_blueprint(build_root_routes())
    app.register_blueprint(build_produto_routes(ProdutoController(produtos)))
    app.register_blueprint(build_usuario_routes(UsuarioController(usuarios)))
    app.register_blueprint(build_pedido_routes(PedidoController(pedidos, produtos, NotificationService())))
    app.register_blueprint(build_relatorio_routes(RelatorioController(RelatorioModel(get_db))))
    app.register_blueprint(build_health_routes(HealthController(produtos, usuarios, pedidos, app.config)))
    app.register_blueprint(build_admin_routes(AdminController(AdminModel(get_db))))

    register_error_handlers(app)
    _warn_insecure_defaults(app.config)
    return app


app = create_app()

if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", Settings.HOST, Settings.PORT)
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
