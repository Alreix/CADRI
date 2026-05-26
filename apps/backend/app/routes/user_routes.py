from flask import Blueprint, jsonify

users_bp = Blueprint("users", __name__)


@users_bp.get("/health")
def users_health():
    return jsonify({"message": "User routes working"}), 200
