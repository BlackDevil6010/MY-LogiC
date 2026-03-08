import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from extensions import db, bcrypt, jwt


def create_app():
    app = Flask(_name_)
    app.config.from_object(Config)

    # -------------------------
    # Logging
    # -------------------------
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # -------------------------
    # Initialize extensions
    # -------------------------
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # -------------------------
    # CORS Configuration
    # -------------------------
    frontend_url_raw = os.environ.get("FRONTEND_URL", "").strip()
    frontend_url = frontend_url_raw.rstrip("/") if frontend_url_raw else ""

    if frontend_url:
        app.logger.info(f"CORS: Configuring for origin -> {frontend_url}")

        CORS(
            app,
            resources={r"/api/*": {"origins": [frontend_url]}},
            supports_credentials=True,
            allow_headers=["Content-Type", "Authorization"],
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )

    else:
        app.logger.warning("CORS: FRONTEND_URL not set. Allowing all origins (Development Mode).")

        CORS(
            app,
            resources={r"/api/": {"origins": ""}},
            allow_headers=["Content-Type", "Authorization"],
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )

    # -------------------------
    # Handle Preflight Requests
    # -------------------------
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            headers = response.headers

            headers["Access-Control-Allow-Origin"] = os.environ.get("FRONTEND_URL", "*")
            headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

            return response

    # -------------------------
    # Force CORS headers
    # -------------------------
    @app.after_request
    def add_cors_headers(response):
        origin = os.environ.get("FRONTEND_URL", "*")

        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

        return response

    # -------------------------
    # Ensure upload folder exists
    # -------------------------
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # -------------------------
    # Import models and create tables
    # -------------------------
    with app.app_context():
        try:
            import models.models  # noqa
            app.logger.info("Creating DB tables (if they don't exist)")
            db.create_all()
            app.logger.info("Database tables ready")
        except Exception as e:
            app.logger.exception("Failed to initialize database: %s", e)

    # -------------------------
    # Register blueprints
    # -------------------------
    try:
        from routes.auth_routes import bp as auth_bp
        from routes.contract_routes import bp as contract_bp

        app.register_blueprint(auth_bp, url_prefix="/api/auth")
        app.register_blueprint(contract_bp, url_prefix="/api")

    except Exception as e:
        app.logger.exception("Failed to register blueprints: %s", e)

    # -------------------------
    # Root Route
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
# Gunicorn Entrypoint
# -------------------------
app = create_app()

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
