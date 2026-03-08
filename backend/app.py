import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, bcrypt, jwt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    CORS(app)

    # Ensure upload folder exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    with app.app_context():
        from models import User, Contract, Clause, RiskFlag
        db.create_all()
        print("✅ Tables created successfully")

    from routes.contract_routes import bp as contract_bp
    from routes.auth_routes import bp as auth_bp

    app.register_blueprint(contract_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    @app.route("/")
    def index():
        return jsonify({"status": "Backend API running successfully"})

    return app


app = create_app()
