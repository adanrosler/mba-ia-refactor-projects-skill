from flask import Blueprint, current_app, jsonify


def build_root_routes():
    bp = Blueprint("root", __name__)

    @bp.get("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": current_app.config["APP_VERSION"],
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    return bp
