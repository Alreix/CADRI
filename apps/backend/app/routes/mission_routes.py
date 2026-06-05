"""Mission routes exposed through Flask-RESTX."""

from flask_restx import Namespace, Resource


missions_ns = Namespace("missions", description="Mission operations")


@missions_ns.route("/health")
class MissionsHealthResource(Resource):
    def get(self):
        """Return the mission namespace health status."""
        return {"message": "Mission routes working"}, 200