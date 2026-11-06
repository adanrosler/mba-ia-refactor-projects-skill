from flask import Blueprint, jsonify

from middlewares.auth import require_admin


def build_relatorio_blueprint(controller):
    bp = Blueprint("relatorios", __name__)

    @bp.get("/relatorios/vendas")
    @require_admin
    def relatorio_vendas():
        return jsonify({"dados": controller.vendas(), "sucesso": True}), 200

    return bp
