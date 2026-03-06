import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

# =========================
# Extensions
# =========================
db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__)

    # =========================
    # Configuration
    # =========================
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key")
    app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        database_url = database_url.strip()

        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+psycopg2://", 1
            )

        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///local.db"

    # =========================
    # Initialize Extensions
    # =========================
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # =========================
    # Import Models (IMPORTANT)
    # =========================
    from models.models import User

    # =========================
    # CREATE TABLES (VERY IMPORTANT)
    # =========================
    with app.app_context():
        db.create_all()

    # =========================
    # Register Blueprints
    # =========================
    from routes.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # =========================
    # Health Check
    # =========================
    @app.route("/")
    def health():
        return jsonify({"status": "Backend Running Successfully"})

    return app


# Gunicorn entry point
app = create_app()
