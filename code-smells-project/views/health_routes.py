from flask import Blueprint, jsonify


def build_health_routes(controller):
    bp = Blueprint("health", __name__)

    @bp.get("/health")
    def health_check():
        corpo, saudavel = controller.status()
        return jsonify(corpo), 200 if saudavel else 500

    return bp
