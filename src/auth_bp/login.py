import os
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

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
        "username": "string"
    }
    """
    try:
        data = request.get_json()

        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "Username and password are required"}), 400

        username = data["username"]
        password = data["password"]

        # Verificar credencials
        if username == os.getenv(
            "DEFAULT_ADMIN_USER", "admin"
        ) and password == os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123"):
            # Generar token JWT
            payload = {
                "username": username,
                "exp": datetime.utcnow() + timedelta(hours=24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return (
                jsonify(
                    {
                        "token": token,
                        "username": username,
                        "message": "Login successful",
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500
