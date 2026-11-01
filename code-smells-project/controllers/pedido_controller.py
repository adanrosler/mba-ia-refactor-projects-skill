import logging

from errors import ValidationError
from models.pedido_model import calcular_total
from validators.pedido_validator import validar_pedido, validar_status

logger = logging.getLogger(__name__)


class PedidoController:
    def __init__(self, pedidos, produtos, notifier):
        self.pedidos = pedidos
        self.produtos = produtos
        self.notifier = notifier

    def criar(self, dados):
        usuario_id, itens = validar_pedido(dados)
        produtos = self.produtos.buscar_por_ids([item["produto_id"] for item in itens])
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado",
                                      payload={"sucesso": False})
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError("Estoque insuficiente para " + produto["nome"],
                                      payload={"sucesso": False})

        total = calcular_total(itens, produtos)
        pedido_id = self.pedidos.criar(usuario_id, itens, produtos, total)
        self.notifier.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_todos(self, limit=None, offset=0):
        return self.pedidos.listar(limit=limit, offset=offset)

    def listar_por_usuario(self, usuario_id):
        return self.pedidos.listar(usuario_id=usuario_id)

    def atualizar_status(self, pedido_id, dados):
        novo_status = validar_status(dados)
        self.pedidos.atualizar_status(pedido_id, novo_status)
        self.notifier.status_pedido_alterado(pedido_id, novo_status)
