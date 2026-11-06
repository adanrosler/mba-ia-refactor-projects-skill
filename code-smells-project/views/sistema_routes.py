from flask import Blueprint, jsonify

from middlewares.auth import require_admin
from views.request_utils import json_body


def build_sistema_blueprint(controller):
    bp = Blueprint("sistema", __name__)

    @bp.get("/health")
    def health_check():
        corpo, status = controller.health()
        return jsonify(corpo), status

    @bp.post("/admin/reset-db")
    @require_admin
    def reset_database():
        controller.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @bp.post("/admin/query")
    @require_admin
    def executar_query():
        resultado = controller.executar_query(json_body())
        if resultado is None:
            return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
        return jsonify({"dados": resultado, "sucesso": True}), 200

    return bp
