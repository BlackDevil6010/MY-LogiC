import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from extensions import db, bcrypt, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ----------------------------
    # LOGGING (important for Railway)
    # ----------------------------
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # ----------------------------
    # INITIALIZE EXTENSIONS
    # ----------------------------
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # ----------------------------
    # CORS FIX (FINAL VERSION)
    # ----------------------------
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    @app.after_request
    def after_request(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    # ----------------------------
    # ENSURE UPLOAD FOLDER EXISTS
    # ----------------------------
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # ----------------------------
    # IMPORT MODELS + CREATE TABLES
    # ----------------------------
    with app.app_context():
        try:
            import models.models  # IMPORTANT: do NOT call create_app inside models
            db.create_all()
            app.logger.info("✅ Database tables ready.")
        except Exception as e:
            app.logger.exception("❌ Database initialization failed: %s", e)

    # ----------------------------
    # REGISTER BLUEPRINTS
    # ----------------------------
    from routes.auth_routes import bp as auth_bp
    from routes.contract_routes import bp as contract_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(contract_bp, url_prefix="/api")

    # ----------------------------
    # ROOT ROUTE
    # ----------------------------
    @app.route("/")
    def index():
        return jsonify({"status": "Backend API running successfully"})

    # ----------------------------
    # ERROR HANDLERS (Return JSON, not HTML)
    # ----------------------------
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not Found"}), 404
        return "Not Found", 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception("Internal Server Error: %s", error)
        return jsonify({"error": "Internal Server Error"}), 500

    return app


# Gunicorn entry point (Railway uses this)
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
