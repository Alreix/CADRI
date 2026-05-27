from flask import Blueprint, jsonify

missions_bp = Blueprint("missions", __name__)


@missions_bp.get("/health")
def missions_health():
    return jsonify({"message": "Mission routes working"}), 200
