import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # ======================
    # Configuration
    # ======================

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

    # ======================
    # Init Extensions
    # ======================

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # ======================
    # Register Blueprints
    # ======================

    from routes.auth_routes import bp as auth_bp
    from routes.contract_routes import bp as contract_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(contract_bp, url_prefix="/api")

    # ======================
    # Health Check
    # ======================

    @app.route("/")
    def health_check():
        return jsonify({"status": "Backend Running"})

    return app


app = create_app()
