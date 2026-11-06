from flask import Blueprint, jsonify

from middlewares.auth import require_admin
from views.request_utils import json_body, paginacao


def build_pedido_blueprint(controller):
    bp = Blueprint("pedidos", __name__)

    @bp.post("/pedidos")
    def criar_pedido():
        resultado = controller.criar(json_body())
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    @bp.get("/pedidos")
    @require_admin
    def listar_todos_pedidos():
        return jsonify({"dados": controller.listar(*paginacao()), "sucesso": True}), 200

    @bp.get("/pedidos/usuario/<int:usuario_id>")
    def listar_pedidos_usuario(usuario_id):
        return jsonify({"dados": controller.listar_por_usuario(usuario_id), "sucesso": True}), 200

    @bp.put("/pedidos/<int:pedido_id>/status")
    @require_admin
    def atualizar_status_pedido(pedido_id):
        controller.atualizar_status(pedido_id, json_body())
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    return bp
