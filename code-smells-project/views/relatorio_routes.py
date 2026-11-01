from flask import Blueprint, jsonify

from middlewares.auth import admin_token_required


def build_relatorio_routes(controller):
    bp = Blueprint("relatorios", __name__)

    @bp.get("/relatorios/vendas")
    @admin_token_required
    def relatorio_vendas():
        return jsonify({"dados": controller.vendas(), "sucesso": True}), 200

    return bp
