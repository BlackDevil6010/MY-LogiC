import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("DATABASE_URL not set, using SQLite fallback")
        db_path = os.path.join(basedir, "instance", "contract_analyzer.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        database_url = f"sqlite:///{db_path}"

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    is_postgres = database_url.startswith("postgresql://")

    # Hosted PostgreSQL (Render, Neon, Supabase) requires SSL and connection pooling options
    if is_postgres:
        is_local = "localhost" in database_url or "127.0.0.1" in database_url
        if not is_local and "sslmode" not in database_url:
            separator = "&" if "?" in database_url else "?"
            database_url = f"{database_url}{separator}sslmode=require"

        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
    else:
        # SQLite engine options (do not pass sslmode)
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
        }

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
