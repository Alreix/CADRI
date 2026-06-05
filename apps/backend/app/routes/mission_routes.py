"""Mission-related routes (placeholder).

This module exposes a lightweight blueprint used as a placeholder while the
missions domain is being implemented. It provides a health endpoint and is
kept intentionally minimal to avoid coupling tests to incomplete business
logic.
"""

from flask import Blueprint, jsonify


missions_bp = Blueprint("missions", __name__)


@missions_bp.get("/health")
def missions_health():
    """Simple runtime health endpoint for mission routes."""
    return jsonify({"message": "Mission routes working"}), 200
