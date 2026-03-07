from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
from models import db
from models.models import User
import datetime

bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 409

    # Hash the password
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    new_user = User(email=email, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    # Generate token automatically so the user is logged in
    access_token = create_access_token(identity=str(new_user.id), expires_delta=datetime.timedelta(days=1))
    
    return jsonify({"message": "User registered successfully", "token": access_token}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=str(user.id), expires_delta=datetime.timedelta(days=1))
    
    return jsonify({"message": "Login successful", "token": access_token}), 200
