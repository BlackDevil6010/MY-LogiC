import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    # Fix Railway postgres prefix issue
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "uploads"

    # ✅ Gmail SMTP Settings
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True

    # ⚠️ IMPORTANT: Replace with YOUR Gmail
    MAIL_USERNAME = "yugeshdhanasekaran@gmail.com"

    # ⚠️ IMPORTANT: Replace with your Gmail App Password (NO spaces)
    MAIL_PASSWORD = "xrhvwtcarvxkxxib"

    MAIL_DEFAULT_SENDER = MAIL_USERNAME
