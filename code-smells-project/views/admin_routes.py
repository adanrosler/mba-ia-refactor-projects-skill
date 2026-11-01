from flask import Blueprint, jsonify, request

from middlewares.auth import admin_tools_required


def build_admin_routes(controller):
    bp = Blueprint("admin", __name__)

    @bp.post("/admin/reset-db")
    @admin_tools_required
    def reset_database():
        controller.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @bp.post("/admin/query")
    @admin_tools_required
    def executar_query():
        resultado = controller.executar_query(request.get_json(silent=True))
        if resultado is None:
            return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
        return jsonify({"dados": resultado, "sucesso": True}), 200

    return bp
