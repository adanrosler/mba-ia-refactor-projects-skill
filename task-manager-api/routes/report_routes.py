from flask import Blueprint, jsonify

from models.user import ROLE_ADMIN, ROLE_MANAGER

REPORT_ROLES = (ROLE_ADMIN, ROLE_MANAGER)


def build_report_routes(controller, auth):
    bp = Blueprint('reports', __name__)

    @bp.get('/reports/summary')
    @auth.required(roles=REPORT_ROLES)
    def summary_report():
        return jsonify(controller.summary()), 200

    @bp.get('/reports/user/<int:user_id>')
    @auth.required(roles=REPORT_ROLES)
    def user_report(user_id):
        return jsonify(controller.user_report(user_id)), 200

    return bp
