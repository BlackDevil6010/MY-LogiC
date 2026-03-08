# app.py
import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from extensions import db, bcrypt, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # -------------------------
    # Logging Configuration
    # -------------------------
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # -------------------------
    # Initialize Extensions
    # -------------------------
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # -------------------------
    # CORS Configuration
    # -------------------------
    frontend_url_raw = os.environ.get("FRONTEND_URL", "").strip()
    # Normalize by removing trailing slash
    frontend_url = frontend_url_raw.rstrip("/") if frontend_url_raw else ""

    if frontend_url:
        app.logger.info(f"Using FRONTEND_URL for CORS: {frontend_url!r}")
        # Production: Allow specific origin with credentials (for cookies/session if needed)
        CORS(
            app, 
            resources={r"/api/*": {"origins": frontend_url}}, 
            supports_credentials=True
        )
    else:
        app.logger.warning(
            "FRONTEND_URL not set — allowing all origins for /api/* (development only)."
        )
        # Development Fallback:
        # We remove 'supports_credentials=True' here.
        # Browsers block wildcard "*" origins if credentials are allowed.
        # Since your frontend uses localStorage (Bearer tokens), this is the correct setup.
        CORS(app, resources={r"/api/*": {"origins": "*"}})

    # -------------------------
    # Ensure Upload Folder Exists
    # -------------------------
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # -------------------------
    # Database Initialization
    # -------------------------
    with app.app_context():
        try:
            # Ensure models are imported
            import models.models  # noqa
            app.logger.info("Creating DB tables (if they don't exist)")
            db.create_all()
            app.logger.info("Database tables ready")
        except Exception as e:
            app.logger.exception("Failed to initialize database or create tables: %s", e)

    # -------------------------
    # Register Blueprints
    # -------------------------
    try:
        from routes.auth_routes import bp as auth_bp
        from routes.contract_routes import bp as contract_bp

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        app.register_blueprint(contract_bp, url_prefix="/api")
        app.logger.info("Blueprints registered successfully.")
    except Exception as e:
        app.logger.exception("Failed to register blueprints: %s", e)

    # -------------------------
    # Routes
    # -------------------------
    @app.route("/")
    def index():
        return jsonify({"status": "Backend API running successfully"})

    # -------------------------
    # Error Handlers
    # -------------------------
    @app.errorhandler(404)
    def handle_404(err):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not Found"}), 404
        return "Not Found", 404

    @app.errorhandler(500)
    def handle_500(err):
        app.logger.exception("Internal server error: %s", err)
        return jsonify({"error": "Internal Server Error"}), 500

    return app


# -------------------------
# Entrypoint
# -------------------------
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
