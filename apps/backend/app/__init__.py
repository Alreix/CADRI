from flask import Flask

from app.config import get_config
from app.extensions import bcrypt, cors, db, jwt, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    configure_extensions(app)
    configure_routes(app)

    return app


def configure_extensions(app):
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
    from app.routes.auth_routes import auth_bp
    from app.routes.me_routes import me_bp
    from app.routes.metadata_routes import metadata_bp
    from app.routes.mission_routes import missions_bp
    from app.routes.user_routes import users_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(me_bp, url_prefix="/me")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(missions_bp, url_prefix="/missions")
    app.register_blueprint(metadata_bp, url_prefix="/metadata")