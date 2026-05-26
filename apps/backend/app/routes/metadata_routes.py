from flask import Blueprint, jsonify

metadata_bp = Blueprint("metadata", __name__)


@metadata_bp.get("/health")
def metadata_health():
    return jsonify({"message": "Metadata routes working"}), 200
