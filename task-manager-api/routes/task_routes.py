from flask import Blueprint, jsonify, request

from routes.pagination import pagination_args


def build_task_routes(controller, auth):
    bp = Blueprint('tasks', __name__)

    @bp.get('/tasks')
    def get_tasks():
        return jsonify(controller.list_tasks(*pagination_args())), 200

    @bp.get('/tasks/<int:task_id>')
    def get_task(task_id):
        return jsonify(controller.get_task(task_id)), 200

    @bp.post('/tasks')
    @auth.required()
    def create_task():
        return jsonify(controller.create_task(request.get_json())), 201

    @bp.put('/tasks/<int:task_id>')
    @auth.required()
    def update_task(task_id):
        return jsonify(controller.update_task(task_id, request.get_json())), 200

    @bp.delete('/tasks/<int:task_id>')
    @auth.required()
    def delete_task(task_id):
        return jsonify(controller.delete_task(task_id)), 200

    @bp.get('/tasks/search')
    def search_tasks():
        args = request.args
        result = controller.search_tasks(
            args.get('q', ''), args.get('status', ''), args.get('priority', ''), args.get('user_id', ''),
            *pagination_args(),
        )
        return jsonify(result), 200

    @bp.get('/tasks/stats')
    def task_stats():
        return jsonify(controller.stats()), 200

    return bp
