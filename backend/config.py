import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("❌ DATABASE_URL is not set")

    # Fix Railway postgres prefix issue
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "uploads"
        # Email Settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'yugeshdhanasekaran@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'xrhv wtca rvxk xxib')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
