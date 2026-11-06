import logging

from controllers.pagination import limites
from validators.pedido_validator import validar_pedido, validar_status

logger = logging.getLogger(__name__)


class PedidoController:
    def __init__(self, pedidos, notificador):
        self.pedidos = pedidos
        self.notificador = notificador

    def criar(self, dados):
        usuario_id, itens = validar_pedido(dados)
        resultado = self.pedidos.criar(usuario_id, itens)
        self.notificador.pedido_criado(resultado["pedido_id"], usuario_id)
        return resultado

    def listar_por_usuario(self, usuario_id):
        return self.pedidos.listar_por_usuario(usuario_id)

    def listar(self, page=None, per_page=None):
        limit, offset = limites(page, per_page)
        return self.pedidos.listar(limit, offset)

    def atualizar_status(self, pedido_id, dados):
        novo_status = validar_status(dados)
        self.pedidos.atualizar_status(pedido_id, novo_status)
        self.notificador.status_alterado(pedido_id, novo_status)
