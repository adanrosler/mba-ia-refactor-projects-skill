from flask import Blueprint, jsonify

from middlewares.auth import require_admin
from views.request_utils import json_body, paginacao


def build_usuario_blueprint(controller):
    bp = Blueprint("usuarios", __name__)

    @bp.get("/usuarios")
    @require_admin
    def listar_usuarios():
        return jsonify({"dados": controller.listar(*paginacao()), "sucesso": True}), 200

    @bp.get("/usuarios/<int:id>")
    @require_admin
    def buscar_usuario(id):
        return jsonify({"dados": controller.obter(id), "sucesso": True}), 200

    @bp.post("/usuarios")
    def criar_usuario():
        return jsonify({"dados": controller.criar(json_body()), "sucesso": True}), 201

    @bp.post("/login")
    def login():
        usuario = controller.login(json_body())
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

    return bp
