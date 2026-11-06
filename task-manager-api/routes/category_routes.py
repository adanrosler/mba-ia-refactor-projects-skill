from flask import Blueprint, jsonify, request

from middlewares.auth import require_auth
from utils.constants import ROLE_ADMIN
from validators.common import parse_pagination


def create_category_blueprint(controller):
    category_bp = Blueprint('categories', __name__)

    @category_bp.route('/categories', methods=['GET'])
    def get_categories():
        page, per_page = parse_pagination(request.args)
        return jsonify(controller.list_categories(page, per_page)), 200

    @category_bp.route('/categories', methods=['POST'])
    def create_category():
        return jsonify(controller.create_category(request.get_json())), 201

    @category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
    def update_category(cat_id):
        return jsonify(controller.update_category(cat_id, request.get_json())), 200

    @category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
    @require_auth(roles=(ROLE_ADMIN,))
    def delete_category(cat_id):
        return jsonify(controller.delete_category(cat_id)), 200

    return category_bp
