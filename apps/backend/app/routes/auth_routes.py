from flask import Blueprint, jsonify

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/health")
def auth_health():
    return jsonify({"message": "Auth routes working"}), 200
