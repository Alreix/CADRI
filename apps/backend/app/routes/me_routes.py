from flask import Blueprint, jsonify

me_bp = Blueprint("me", __name__)


@me_bp.get("/health")
def me_health():
    return jsonify({"message": "Me routes working"}), 200
