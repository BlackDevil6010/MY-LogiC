import os
import sys

# Add the current directory to sys.path to import from backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.models import User, Contract, Clause, RiskFlag, StandardClause


def init_database():
    app = create_app()
    with app.app_context():
        print("Initializing database tables...")
        db.create_all()
        print("Tables created successfully.")

        user_count = User.query.count()
        print(f"Database ready. Existing users: {user_count}")


if __name__ == "__main__":
    init_database()
