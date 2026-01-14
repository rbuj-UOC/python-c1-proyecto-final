import os
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from database import get_db
from models import User

login_bp = Blueprint("login", __name__)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")


@login_bp.route("/login", methods=["POST"])
def login():
    """
    Endpoint per autenticar un usuari

    Petició JSON:
    {
        "username": "string",
        "password": "string"
    }

    Resposta JSON:
    {
        "token": "bearer_token",
        "username": "string",
        "rol": "string"
    }
    """
    try:
        data = request.get_json()

        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "Username and password are required"}), 400

        username = data["username"]
        password = data["password"]

        # Consultar l'usuari a la base de dades
        db = get_db()
        user = db.query(User).filter(User.username == username).first()

        if user and check_password_hash(user.password, password):
            # Generar token JWT amb informació de l'usuari
            payload = {
                "id_user": user.id_user,
                "username": user.username,
                "rol": user.rol.value,
                "exp": datetime.utcnow() + timedelta(hours=24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return (
                jsonify(
                    {
                        "token": token,
                        "username": user.username,
                        "rol": user.rol.value,
                        "message": "Login successful",
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500
