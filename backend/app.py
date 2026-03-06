import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions globally
db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    # ==============================
    # Environment Configuration
    # ==============================

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key")
    app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]

    # Get database URL from environment (Railway variable)
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable not set")

    # Supabase sometimes needs explicit psycopg2 driver
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://", "postgresql+psycopg2://", 1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["UPLOAD_FOLDER"] = "uploads"

    # ==============================
    # Extensions Init
    # ==============================

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ==============================
    # Create Tables on Startup
    # ==============================

    with app.app_context():
        db.create_all()

    # ==============================
    # Health Check Route
    # ==============================

    @app.route("/")
    def health_check():
        return jsonify({
            "status": "MY-LogiC Backend Running",
            "database": "Connected",
            "environment": "Production"
        })

    return app


# ==============================
# Run Locally
# ==============================

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
