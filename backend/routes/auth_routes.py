import datetime
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db, bcrypt
from models.models import User

logger = logging.getLogger(__name__)
bp = Blueprint("auth", __name__)


# -------------------------
# REGISTER
# -------------------------
@bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        email = (data.get("email") or "").strip().lower()
        password = (data.get("password") or "").strip()

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "An account with this email already exists"}), 409

        # Hash password
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(email=email, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(
            identity=str(new_user.id),
            expires_delta=datetime.timedelta(days=7)
        )

        return jsonify({
            "message": "User registered successfully",
            "token": access_token,
            "email": new_user.email
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.exception("Register error: %s", e)
        # Return helpful error message to diagnose DB/environment issues
        return jsonify({"error": f"Database/Server error: {str(e)}"}), 500


# -------------------------
# LOGIN
# -------------------------
@bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        email = (data.get("email") or "").strip().lower()
        password = (data.get("password") or "").strip()

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid email or password"}), 401

        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=datetime.timedelta(days=7)
        )

        return jsonify({
            "message": "Login successful",
            "token": access_token,
            "email": user.email
        }), 200

    except Exception as e:
        logger.exception("Login error: %s", e)
        return jsonify({"error": f"Database/Server error: {str(e)}"}), 500


# -------------------------
# CURRENT USER
# -------------------------
@bp.route("/current-user", methods=["GET"])
@jwt_required()
def get_current_user():
    try:
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }), 200
    except Exception as e:
        logger.exception("Current user error: %s", e)
        return jsonify({"error": str(e)}), 500
