from flask import Blueprint, g, jsonify, request

from middlewares.auth import current_user_or_none, require_auth
from utils.constants import ROLE_ADMIN
from validators.common import parse_pagination


def create_user_blueprint(controller):
    user_bp = Blueprint('users', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        page, per_page = parse_pagination(request.args)
        return jsonify(controller.list_users(page, per_page)), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        return jsonify(controller.get_user(user_id)), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        # Papel padrão continua público; papel privilegiado é autorizado no controller.
        return jsonify(controller.create_user(request.get_json(), actor=current_user_or_none())), 201

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    @require_auth()
    def update_user(user_id):
        return jsonify(controller.update_user(user_id, request.get_json(), actor=g.current_user)), 200

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    @require_auth(roles=(ROLE_ADMIN,))
    def delete_user(user_id):
        return jsonify(controller.delete_user(user_id)), 200

    @user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        return jsonify(controller.list_user_tasks(user_id)), 200

    @user_bp.route('/login', methods=['POST'])
    def login():
        return jsonify(controller.login(request.get_json())), 200

    return user_bp
