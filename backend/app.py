# app.py
import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from extensions import db, bcrypt, jwt
from sqlalchemy import text


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    app.logger.setLevel(logging.INFO)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # -------------------------
    # CORS Configuration
    # -------------------------
    frontend_url_raw = os.environ.get("FRONTEND_URL", "").strip()
    frontend_url = frontend_url_raw.rstrip("/") if frontend_url_raw else ""

    allowed_origins = [
        "https://my-logic.vercel.app",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5500",
    ]
    if frontend_url and frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)

    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins if frontend_url else "*"}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # Ensure upload folder exists
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # Import models and create tables
    with app.app_context():
        try:
            import models.models  # noqa
            app.logger.info("Initializing database tables...")
            db.create_all()
            app.logger.info("Database tables initialized successfully")
        except Exception as e:
            app.logger.exception("Database initialization warning: %s", e)

    # Register blueprints
    try:
        from routes.auth_routes import bp as auth_bp
        from routes.contract_routes import bp as contract_bp

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        app.register_blueprint(contract_bp, url_prefix="/api")
    except Exception as e:
        app.logger.exception("Failed to register blueprints: %s", e)

    # -------------------------
    # Root & Health Routes
    # -------------------------
    @app.route("/")
    def index():
        return jsonify({
            "status": "online",
            "message": "Contract AI Backend API is running successfully",
            "timestamp": datetime.utcnow().isoformat()
        })

    @app.route("/api/health")
    def health():
        db_status = "ok"
        db_error = None
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            db_status = "error"
            db_error = str(e)

        status_code = 200 if db_status == "ok" else 503
        return jsonify({
            "status": "healthy" if db_status == "ok" else "degraded",
            "database": db_status,
            "database_error": db_error,
            "timestamp": datetime.utcnow().isoformat()
        }), status_code

    # -------------------------
    # Error Handlers
    # -------------------------
    @app.errorhandler(404)
    def handle_404(err):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Endpoint not found"}), 404
        return "Not Found", 404

    @app.errorhandler(500)
    def handle_500(err):
        app.logger.exception("Internal server error: %s", err)
        return jsonify({"error": "Internal Server Error"}), 500

    return app


# Gunicorn entrypoint
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
