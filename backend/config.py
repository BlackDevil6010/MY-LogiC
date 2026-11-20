import os
import logging
import psycopg2

logger = logging.getLogger(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))


def is_postgres_reachable(url):
    """Test if the PostgreSQL URL is alive and reachable with a 2-second timeout."""
    try:
        conn = psycopg2.connect(url, connect_timeout=2)
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️ PostgreSQL unreachable ({e}). Falling back to SQLite.")
        return False


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    database_url = os.getenv("DATABASE_URL")

    db_path = os.path.join(basedir, "instance", "contract_analyzer.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    sqlite_fallback_url = f"sqlite:///{db_path}"

    active_url = sqlite_fallback_url
    is_postgres = False

    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        if database_url.startswith("postgresql://"):
            is_local = "localhost" in database_url or "127.0.0.1" in database_url
            formatted_url = database_url
            if not is_local and "sslmode" not in formatted_url:
                sep = "&" if "?" in formatted_url else "?"
                formatted_url = f"{formatted_url}{sep}sslmode=require"

            # Verify PostgreSQL is reachable; otherwise fall back gracefully to SQLite
            if is_postgres_reachable(formatted_url):
                active_url = formatted_url
                is_postgres = True
            else:
                active_url = sqlite_fallback_url
                is_postgres = False

    if is_postgres:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
        }

    SQLALCHEMY_DATABASE_URI = active_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    IS_POSTGRES = is_postgres
