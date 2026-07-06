from flask import Blueprint, jsonify
from core.database import get_db
from services import health_service

bp = Blueprint('health', __name__)

@bp.route("/health")
def health():
    return jsonify(health_service.check_liveness()), 200

@bp.route("/ready")
def ready():
    try:
        with get_db() as db:
            result = health_service.check_readiness(db)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "not ready", "reason": str(e)}), 503
