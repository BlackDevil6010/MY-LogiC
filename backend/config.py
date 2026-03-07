import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    SUPABASE_DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")

    if not SUPABASE_DATABASE_URL:
        raise RuntimeError("❌ SUPABASE_DATABASE_URL environment variable is NOT set")

    SQLALCHEMY_DATABASE_URI = SUPABASE_DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "uploads"
