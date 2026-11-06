from flask import Blueprint, jsonify

from middlewares.auth import require_auth
from utils.constants import REPORT_ROLES


def create_report_blueprint(controller):
    report_bp = Blueprint('reports', __name__)

    @report_bp.route('/reports/summary', methods=['GET'])
    @require_auth(roles=REPORT_ROLES)
    def summary_report():
        return jsonify(controller.summary()), 200

    @report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
    @require_auth(roles=REPORT_ROLES)
    def user_report(user_id):
        return jsonify(controller.user_report(user_id)), 200

    return report_bp
