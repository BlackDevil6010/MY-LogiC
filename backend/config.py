import os



class Config:

    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")



    database_url = os.getenv("DATABASE_URL")



    # Fallback for safety (optional but recommended)

    if not database_url:

        print("⚠️ DATABASE_URL not set, using SQLite (temporary)")

        database_url = "sqlite:///local.db"



    if database_url.startswith("postgres://"):

        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "uploads"

