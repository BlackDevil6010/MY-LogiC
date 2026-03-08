# app.py
import os
import logging
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from config import Config
from extensions import db, bcrypt, jwt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # CORS: read allowed origin from env
    frontend_url = os.environ.get("FRONTEND_URL", None)

    if frontend_url:
        app.logger.info(f"Using FRONTEND_URL for CORS: {frontend_url}")
        CORS(app, resources={r"/api/*": {"origins": frontend_url}}, supports_credentials=True)
    else:
        app.logger.warning("FRONTEND_URL not set — allowing all origins for /api/* (development only).")
        CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Ensure upload folder exists
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # Import models and create tables (inside app_context)
    with app.app_context():
        try:
            # IMPORTANT: models.models should NOT call create_app() (avoid circular import)
            import models.models  # noqa
            app.logger.info("Creating DB tables (if they don't exist)")
            db.create_all()
            app.logger.info("Database tables ready")
        except Exception as e:
            app.logger.exception("Failed to initialize database or create tables: %s", e)

    # Register blueprints
    try:
        from routes.auth_routes import bp as auth_bp
        from routes.contract_routes import bp as contract_bp

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        app.register_blueprint(contract_bp, url_prefix="/api")
    except Exception as e:
        app.logger.exception("Failed to register blueprints: %s", e)

    # Root
    @app.route("/")
    def index():
        return jsonify({"status": "Backend API running successfully"})

    # Add CORS headers again as a defensive fallback for any response (ensures preflight ok)
    @app.after_request
    def add_cors_headers(response):
        origin = os.environ.get("FRONTEND_URL", "*")
        # If FRONTEND_URL is "*", set wildcard. Otherwise set the explicit origin.
        if origin == "*":
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    # Return JSON for API 404/500 instead of HTML (helps frontend)
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

# Gunicorn entrypoint
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
