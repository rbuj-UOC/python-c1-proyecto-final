import os
import jwt
from flask import Blueprint, request, jsonify

verify_bp = Blueprint("verify", __name__)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")


@verify_bp.route("/verify", methods=["POST"])
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
        "username": "string"
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
                jsonify({"valid": True, "username": payload["username"]}),
                200,
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired", "valid": False}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token", "valid": False}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500
