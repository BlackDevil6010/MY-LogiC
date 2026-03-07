import os
from flask import Flask, jsonify
from flask_cors import CORS
from extensions import db, jwt, bcrypt


def create_app():
    app = Flask(__name__)

    # =========================
    # Basic Configuration
    # =========================
    app.config["SECRET_KEY"] = "super-secret-key"
    app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]

    # ✅ Local SQLite Database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///local.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # =========================
    # Initialize Extensions
    # =========================
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # =========================
    # Import Models
    # =========================
    from models.models import User, Contract, Clause, RiskFlag

    # =========================
    # Create Tables
    # =========================
    with app.app_context():
        db.create_all()

    # =========================
    # Register Blueprints
    # =========================
    from routes.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # =========================
    # Health Check Route
    # =========================
    @app.route("/")
    def health():
        return jsonify({"status": "Backend Running (SQLite Mode)"})

    return app


# Gunicorn entry
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
