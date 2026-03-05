import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db
from services.risk_analyzer import RiskAnalyzer


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # JWT secret key
    app.config["JWT_SECRET_KEY"] = app.config.get("SECRET_KEY", "default-jwt-secret")

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    with app.app_context():
        # Preload Legal BERT model once at startup
        RiskAnalyzer.get_instance()

        # Create database tables
        from models import models
        db.create_all()

    # Import and register routes
    from routes.contract_routes import bp as contract_bp
    from routes.auth_routes import bp as auth_bp

    app.register_blueprint(contract_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # Health check route
    @app.route("/")
    def index():
        return jsonify({
            "status": "MY-LogiC Backend API running",
            "message": "Visit frontend to use the application"
        })

    return app


# Run locally (Railway will use gunicorn instead)
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
