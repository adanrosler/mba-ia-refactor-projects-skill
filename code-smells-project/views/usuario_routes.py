from flask import Blueprint, jsonify, request

from middlewares.auth import admin_token_required
from views.pagination import pagination_args


def build_usuario_routes(controller):
    bp = Blueprint("usuarios", __name__)

    @bp.get("/usuarios")
    @admin_token_required
    def listar_usuarios():
        return jsonify({"dados": controller.listar(*pagination_args()), "sucesso": True}), 200

    @bp.get("/usuarios/<int:usuario_id>")
    def buscar_usuario(usuario_id):
        return jsonify({"dados": controller.obter(usuario_id), "sucesso": True}), 200

    @bp.post("/usuarios")
    def criar_usuario():
        usuario_id = controller.criar(request.get_json(silent=True))
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    @bp.post("/login")
    def login():
        usuario = controller.login(request.get_json(silent=True))
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

    return bp
