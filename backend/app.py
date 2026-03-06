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

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Supabase fix
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+psycopg2://", 1
            )

        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        # Fallback for safety (prevents crash)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fallback.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = "uploads"

    # ==============================
    # Extensions Init
    # ==============================

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ==============================
    # Create Tables Safely
    # ==============================

    with app.app_context():
        try:
            db.create_all()
            print("✅ Database connected successfully")
        except Exception as e:
            print("❌ Database connection failed:", e)

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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
