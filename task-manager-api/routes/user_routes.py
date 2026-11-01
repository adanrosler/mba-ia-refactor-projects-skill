from flask import Blueprint, jsonify, request

from models.user import ROLE_ADMIN
from routes.pagination import pagination_args


def build_user_routes(controller, auth):
    bp = Blueprint('users', __name__)

    @bp.get('/users')
    @auth.required()
    def get_users():
        return jsonify(controller.list_users(*pagination_args())), 200

    @bp.get('/users/<int:user_id>')
    @auth.required()
    def get_user(user_id):
        return jsonify(controller.get_user(user_id)), 200

    @bp.post('/users')
    @auth.optional
    def create_user():
        return jsonify(controller.create_user(request.get_json(), auth.current_user())), 201

    @bp.put('/users/<int:user_id>')
    @auth.required()
    def update_user(user_id):
        return jsonify(controller.update_user(user_id, request.get_json(), auth.current_user())), 200

    @bp.delete('/users/<int:user_id>')
    @auth.required(roles=(ROLE_ADMIN,))
    def delete_user(user_id):
        return jsonify(controller.delete_user(user_id)), 200

    @bp.get('/users/<int:user_id>/tasks')
    @auth.required()
    def get_user_tasks(user_id):
        return jsonify(controller.list_user_tasks(user_id)), 200

    @bp.post('/login')
    def login():
        return jsonify(controller.login(request.get_json())), 200

    return bp
