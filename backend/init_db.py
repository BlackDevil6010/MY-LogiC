import os
import sys

# Add the current directory to sys.path to import from backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.models import User

def init_database():
    app = create_app()
    with app.app_context():
        print("Initializing database...")
        db.create_all()
        print("Tables created successfully.")
        
        # Check if users already exist
        if User.query.first() is None:
            print("Database is empty. You can now register through the frontend!")
        else:
            print("Database already contains records.")

if __name__ == "__main__":
    init_database()
