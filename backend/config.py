import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("❌ DATABASE_URL is not set in environment")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "uploads"
