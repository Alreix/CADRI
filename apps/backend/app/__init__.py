from datetime import datetime, timezone

from flask import Flask
from flask_restx import Api

from app.config import get_config
from app.extensions import bcrypt, cors, db, jwt, migrate
from app.repositories.token_blocklist_repository import TokenBlocklistRepository
from app.repositories.user_repository import UserRepository


def _as_utc(value):
    """Normalize a database datetime to an aware UTC value for JWT checks."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def configure_jwt_blocklist():
    """Reject revoked JWTs and tokens predating session invalidation events."""

    @jwt.token_in_blocklist_loader
    def is_access_token_revoked(jwt_header, jwt_payload):
        """Fail securely when access-token revocation cannot be disproved."""

        del jwt_header
        if jwt_payload.get("type") != "access":
            return False

        try:
            jti = jwt_payload.get("jti")
            identity = jwt_payload.get("sub")
            issued_at = jwt_payload.get("iat")
            if not jti or not identity or issued_at is None:
                return True
            if TokenBlocklistRepository.is_revoked(jti):
                return True

            user = UserRepository.get_by_id(identity)
            if user is None:
                return True
            if user.tokens_valid_after is None:
                return False

            token_issued_at = datetime.fromtimestamp(issued_at, tz=timezone.utc)
            return token_issued_at < _as_utc(user.tokens_valid_after)
        except (TypeError, ValueError):
            return True


def create_app():
    """Create and configure the Flask application instance.

    The factory loads the environment-specific configuration, initializes
    extensions, and registers all API namespaces before returning the app.
    """
    app = Flask(__name__)
    app.config.from_object(get_config())

    configure_extensions(app)
    configure_routes(app)

    return app


def configure_extensions(app):
    """Attach shared Flask extensions to the application."""
    db.init_app(app)
    migrate.init_app(app, db)

    cors.init_app(
        app,
        resources={r"/*": {"origins": app.config["FRONTEND_URL"]}},
        supports_credentials=True,
    )

    jwt.init_app(app)
    configure_jwt_blocklist()
    bcrypt.init_app(app)


def configure_routes(app):
    """Register every RESTX namespace on the API root."""
    api = Api(app, title="CADRI API", version="1.0", doc="/docs")

    from app.routes.auth_routes import auth_ns
    from app.routes.me_routes import me_ns
    from app.routes.metadata_routes import metadata_ns
    from app.routes.mission_routes import missions_ns
    from app.routes.user_routes import users_ns

    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(me_ns, path="/me")
    api.add_namespace(users_ns, path="/users")
    api.add_namespace(metadata_ns, path="/metadata")
    api.add_namespace(missions_ns, path="/missions")
