import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from services.risk_analyzer import RiskAnalyzer

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Needs to match the secret key config for JWT
    app.config['JWT_SECRET_KEY'] = app.config.get('SECRET_KEY', 'default-jwt-secret')
    
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    db.init_app(app)
    jwt = JWTManager(app)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.app_context():
        # Preload Legal BERT singleton at startup
        RiskAnalyzer.get_instance()
        # Initialize DB tables
        from models import models
        db.create_all()
        
    from routes.contract_routes import bp as contract_bp
    from routes.auth_routes import bp as auth_bp
    
    app.register_blueprint(contract_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    @app.route('/')
    def index():
        return jsonify({"status": "Backend API is running here. Please visit the frontend at http://localhost:8000"})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
