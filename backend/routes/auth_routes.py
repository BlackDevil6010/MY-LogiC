from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from extensions import db, bcrypt
from models.models import User
import datetime

bp = Blueprint("auth", __name__)

# -------------------------
# REGISTER
# -------------------------
@bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "User already exists"}), 409

        # Hash password
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(
            identity=str(new_user.id),
            expires_delta=datetime.timedelta(days=1)
        )

        return jsonify({
            "message": "User registered successfully",
            "token": access_token
        }), 201

    except Exception as e:
        print("REGISTER ERROR:", str(e))
        return jsonify({"error": "Internal server error"}), 500


# -------------------------
# LOGIN
# -------------------------
@bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Missing email or password"}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        if not bcrypt.check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid email or password"}), 401

        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=datetime.timedelta(days=1)
        )

        return jsonify({
            "message": "Login successful",
            "token": access_token
        }), 200

    except Exception as e:
        print("LOGIN ERROR:", str(e))
        return jsonify({"error": "Internal server error"}), 500
