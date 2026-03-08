import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from extensions import db, bcrypt, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Setup logging (Railway logs)
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # ---------------------------
    # CORS CONFIGURATION
    # ---------------------------
    frontend_url = os.environ.get("FRONTEND_URL")

    if frontend_url:
        app.logger.info(f"Using CORS origin: {frontend_url}")
        CORS(
            app,
            resources={r"/api/*": {"origins": frontend_url}},
            supports_credentials=True
        )
    else:
        # Fallback (for testing only)
        app.logger.warning("FRONTEND_URL not set. Allowing all origins.")
        CORS(app, supports_credentials=True)

    # Ensure upload folder exists
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # ---------------------------
    # IMPORT MODELS + CREATE TABLES
    # ---------------------------
    with app.app_context():
        try:
            # IMPORTANT: models file must NOT call create_app()
            import models.models  # noqa

            app.logger.info("Creating database tables...")
            db.create_all()
            app.logger.info("✅ Tables ready.")
        except Exception as e:
            app.logger.exception("Database initialization failed: %s", e)

    # ---------------------------
    # REGISTER BLUEPRINTS
    # ---------------------------
    try:
        from routes.auth_routes import bp as auth_bp
        from routes.contract_routes import bp as contract_bp

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        app.register_blueprint(contract_bp, url_prefix="/api")
    except Exception as e:
        app.logger.exception("Blueprint registration failed: %s", e)

    # Root route
    @app.route("/")
    def index():
        return jsonify({"status": "Backend API running successfully"})

    # Return JSON instead of HTML on server errors
    @app.errorhandler(500)
    def handle_500(error):
        app.logger.exception("Internal server error: %s", error)
        return jsonify({"error": "Internal Server Error"}), 500

    @app.errorhandler(404)
    def handle_404(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not Found"}), 404
        return "Not Found", 404

    return app


# Gunicorn entry point
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
