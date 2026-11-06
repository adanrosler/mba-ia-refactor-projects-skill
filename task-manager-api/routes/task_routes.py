from flask import Blueprint, jsonify, request

from validators.common import parse_optional_int, parse_pagination


def create_task_blueprint(controller):
    task_bp = Blueprint('tasks', __name__)

    @task_bp.route('/tasks', methods=['GET'])
    def get_tasks():
        page, per_page = parse_pagination(request.args)
        return jsonify(controller.list_tasks(page, per_page)), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        return jsonify(controller.get_task(task_id)), 200

    @task_bp.route('/tasks', methods=['POST'])
    def create_task():
        return jsonify(controller.create_task(request.get_json())), 201

    @task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        return jsonify(controller.update_task(task_id, request.get_json())), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        return jsonify(controller.delete_task(task_id)), 200

    @task_bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        args = request.args
        result = controller.search_tasks(
            text=args.get('q', ''),
            status=args.get('status', ''),
            priority=parse_optional_int(args.get('priority'), 'priority'),
            user_id=parse_optional_int(args.get('user_id'), 'user_id'),
        )
        return jsonify(result), 200

    @task_bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.stats()), 200

    return task_bp
