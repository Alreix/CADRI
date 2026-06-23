from flask import Flask
from flask_restx import Api

from app.config import get_config
from app.extensions import bcrypt, cors, db, jwt, migrate


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
