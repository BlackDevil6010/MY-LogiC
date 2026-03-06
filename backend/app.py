import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # ========================
    # Config
    # ========================

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key")
    app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+psycopg2://", 1
            )
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fallback.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ========================
    # Init Extensions
    # ========================

    db.init_app(app)
    jwt.init_app(app)

    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True
    )

    # ========================
    # Register Blueprints
    # ========================

    from routes.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # ========================
    # Health Route
    # ========================

    @app.route("/")
    def health():
        return jsonify({"status": "Backend Running"})

    return app


app = create_app()
