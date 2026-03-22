import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("⚠️ DATABASE_URL not set, using SQLite")
        database_url = "sqlite:///local.db"

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # ✅ IMPORTANT: remove ssl from URL if already added
    database_url = database_url.replace("?sslmode=require", "")

    SQLALCHEMY_DATABASE_URI = database_url

    # ✅ THIS IS THE REAL FIX
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "connect_args": {
            "sslmode": "require"
        }
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "uploads"
