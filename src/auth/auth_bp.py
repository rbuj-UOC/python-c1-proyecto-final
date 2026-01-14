"""Authentication endpoints module."""

import os
from datetime import datetime, timedelta

import jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from database import get_db
from models import User

# Crear blueprint principal d'autenticació
auth_bp = Blueprint("auth", __name__)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")


@auth_bp.route("/login", methods=["POST"])
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

        if user and check_password_hash(str(user.password), password):
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

    except ValueError as e:  # pylint: disable=broad-except
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception:  # pylint: disable=broad-except,unused-variable
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/verify", methods=["POST"])
def verify_token():
    """
    Endpoint per verificar un token

    Petició JSON:
    {
        "token": "bearer_token"
    }

    Resposta JSON:
    {
        "valid": true/false,
        "username": "string",
        "rol": "string",
        "id_user": int
    }
    """
    try:
        data = request.get_json()

        if not data or "token" not in data:
            return jsonify({"error": "Token is required"}), 400

        token = data["token"]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return (
                jsonify(
                    {
                        "valid": True,
                        "username": payload["username"],
                        "rol": payload.get("rol"),
                        "id_user": payload.get("id_user"),
                    }
                ),
                200,
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired", "valid": False}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token", "valid": False}), 401

    except ValueError as e:  # pylint: disable=broad-except
        return jsonify({"error": f"Validation error: {str(e)}", "valid": False}), 400
    except Exception:  # pylint: disable=broad-except,unused-variable
        return jsonify({"error": "Internal server error", "valid": False}), 500
