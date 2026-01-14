"""Authentication endpoints module."""

import os
from datetime import datetime, timedelta

import jwt
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from database import get_db
from models import User

# Crear el blueprint principal d'autenticació
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
        "access_token": "bearer_token",
        "username": "string",
        "role": "string"
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
                "role": user.role.value,
                "exp": datetime.utcnow() + timedelta(hours=24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return (
                jsonify(
                    {
                        "access_token": token,
                        "username": user.username,
                        "role": user.role.value,
                        "message": "Autenticació correcta",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify({"error": "El nom d'usuari o la contrasenya no són vàlids"}),
                401,
            )

    except ValueError as e:
        return jsonify({"error": f"Error de validació: {str(e)}"}), 400
    except Exception:
        return jsonify({"error": "Error intern del servidor"}), 500


@auth_bp.route("/", methods=["GET"])
def verify_token():
    """
    Endpoint per verificar un token

    Capçaleres:
    {
        "Authorization": "Bearer <access_token>"
    }

    Resposta JSON:
    {
        "valid": true/false,
        "username": "string",
        "role": "string",
        "id_user": int
    }
    """
    try:
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return (
                jsonify({"error": "Falta la capçalera Authorization", "valid": False}),
                401,
            )

        # Extreure el token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return (
                jsonify(
                    {
                        "error": "El format de la capçalera Authorization no és vàlid",
                        "valid": False,
                    }
                ),
                401,
            )

        token = parts[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return (
                jsonify(
                    {
                        "valid": True,
                        "username": payload["username"],
                        "role": payload.get("role"),
                        "id_user": payload.get("id_user"),
                    }
                ),
                200,
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "El token ha expirat", "valid": False}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "El token no és vàlid", "valid": False}), 401

    except ValueError as e:
        return jsonify({"error": f"Error de validació: {str(e)}", "valid": False}), 400
    except Exception:
        return jsonify({"error": "Error intern del servidor", "valid": False}), 500
