from flask import Blueprint, jsonify


def create_system_blueprint(controller):
    system_bp = Blueprint('system', __name__)

    @system_bp.route('/health')
    def health():
        return jsonify(controller.health())

    @system_bp.route('/')
    def index():
        return jsonify(controller.index())

    return system_bp
