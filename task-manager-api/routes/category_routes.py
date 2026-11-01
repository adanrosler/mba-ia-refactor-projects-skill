from flask import Blueprint, jsonify, request

from routes.pagination import pagination_args


def build_category_routes(controller, auth):
    bp = Blueprint('categories', __name__)

    @bp.get('/categories')
    def get_categories():
        return jsonify(controller.list_categories(*pagination_args())), 200

    @bp.post('/categories')
    @auth.required()
    def create_category():
        return jsonify(controller.create_category(request.get_json())), 201

    @bp.put('/categories/<int:cat_id>')
    @auth.required()
    def update_category(cat_id):
        return jsonify(controller.update_category(cat_id, request.get_json())), 200

    @bp.delete('/categories/<int:cat_id>')
    @auth.required()
    def delete_category(cat_id):
        return jsonify(controller.delete_category(cat_id)), 200

    return bp
