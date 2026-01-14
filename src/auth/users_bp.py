"""Users management endpoints module."""

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from database import get_db
from decorators import require_auth_role
from models import User, RoleEnum

users_bp = Blueprint("admin", __name__)


@users_bp.route("/usuari", methods=["GET"])
@require_auth_role("admin", "secretaria")
def list_users():
    """
    Endpoint per llistar tots els usuaris

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    {
        "users": [
            {
                "id_user": int,
                "username": "string",
                "role": "string"
            },
            ...
        ]
    }
    """
    try:
        db = get_db()
        users = db.query(User).all()

        users_list = [
            {
                "id_user": user.id_user,
                "username": user.username,
                "role": user.role.value,
            }
            for user in users
        ]

        return jsonify({"users": users_list}), 200

    except ValueError as e:
        return jsonify({"error": f"Error de validació: {str(e)}"}), 400
    except Exception:
        return jsonify({"error": "Error intern del servidor"}), 500


@users_bp.route("/usuari/<int:user_id>", methods=["GET"])
@require_auth_role("admin", "secretaria")
def get_user(user_id):
    """
    Endpoint per obtenir la informació d'un usuari específic

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    {
        "id_user": int,
        "username": "string",
        "role": "string"
    }
    """
    try:
        db = get_db()
        user = db.query(User).filter(User.id_user == user_id).first()

        if not user:
            return jsonify({"error": "Usuari no trobat"}), 404

        return (
            jsonify(
                {
                    "id_user": user.id_user,
                    "username": user.username,
                    "role": user.role.value,
                }
            ),
            200,
        )

    except ValueError as e:  # pylint: disable=broad-except
        return jsonify({"error": f"Error de validació: {str(e)}"}), 400
    except Exception:  # pylint: disable=broad-except
        return jsonify({"error": "Error intern del servidor"}), 500


@users_bp.route("/usuari", methods=["POST"])
@require_auth_role("admin", "secretaria")
def create_user():
    """
    Endpoint per crear un nou usuari

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Petició JSON:
    {
        "username": "string",
        "password": "string",
        "role": "admin|metge|secretaria|pacient"
    }

    Resposta JSON:
    {
        "message": "L'usuari s'ha creat correctament",
        "id_user": int,
        "username": "string",
        "role": "string"
    }
    """
    try:
        data = request.get_json()

        if (
            not data
            or "username" not in data
            or "password" not in data
            or "role" not in data
        ):
            return (
                jsonify({"error": "Es requereixen username, password i role"}),
                400,
            )

        username = data["username"]
        password = data["password"]
        role = data["role"]

        # Validar que el rol sigui vàlid
        try:
            role_enum = RoleEnum[role]
        except KeyError:
            return (
                jsonify(
                    {
                        "error": f"Rol invàlid. Ha de ser un de: {', '.join([r.value for r in RoleEnum])}"
                    }
                ),
                400,
            )

        # Verificar que l'usuari no existeixi
        db = get_db()
        existing_user = db.query(User).filter(User.username == username).first()

        if existing_user:
            return (
                jsonify({"error": "L'usuari ja existeix"}),
                409,
            )

        # Crear el nou usuari
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            role=role_enum,
        )

        db.add(new_user)
        db.commit()

        return (
            jsonify(
                {
                    "message": "L'usuari s'ha creat correctament",
                    "id_user": new_user.id_user,
                    "username": new_user.username,
                    "role": new_user.role.value,
                }
            ),
            201,
        )

    except ValueError as e:  # pylint: disable=broad-except
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception:  # pylint: disable=broad-except
        return jsonify({"error": "Internal server error"}), 500


@users_bp.route("/usuari/<int:user_id>", methods=["PUT"])
@require_auth_role("admin", "secretaria")
def update_user(user_id):
    """
    Endpoint per actualitzar la informació d'un usuari

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Petició JSON:
    {
        "username": "string" (opcional),
        "password": "string" (opcional),
        "role": "admin|metge|secretaria|pacient" (opcional)
    }

    Resposta JSON:
    {
        "message": "S'ha actualitzat l'usuari correctament",
        "id_user": int,
        "username": "string",
        "role": "string"
    }
    """
    try:
        db = get_db()
        user = db.query(User).filter(User.id_user == user_id).first()

        if not user:
            return jsonify({"error": "Usuari no trobat"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "No s'ha proporcionat cap dada"}), 400

        # Actualitzar username si es proporciona
        if "username" in data:
            username = data["username"]

            # Verificar que el nou username no existeixi
            existing_user = (
                db.query(User)
                .filter(User.username == username, User.id_user != user_id)
                .first()
            )

            if existing_user:
                return (
                    jsonify({"error": "El nom d'usuari ja existeix"}),
                    409,
                )

            user.username = username

        # Actualitzar password si es proporciona
        if "password" in data:
            user.password = generate_password_hash(data["password"])

        # Actualitzar role si es proporciona
        if "role" in data:
            role = data["role"]

            try:
                role_enum = RoleEnum[role]
                user.role = role_enum
            except KeyError:
                return (
                    jsonify(
                        {
                            "error": f"Rol invàlid. Ha de ser un de: {', '.join([r.value for r in RoleEnum])}"
                        }
                    ),
                    400,
                )

        db.commit()

        return (
            jsonify(
                {
                    "message": "L'usuari s'ha actualitzat correctament",
                    "id_user": user.id_user,
                    "username": user.username,
                    "role": user.role.value,
                }
            ),
            200,
        )

    except ValueError as e:  # pylint: disable=broad-except
        return jsonify({"error": f"Error de validació: {str(e)}"}), 400
    except Exception:  # pylint: disable=broad-except
        return jsonify({"error": "Error intern del servidor"}), 500


@users_bp.route("/usuari/<int:user_id>", methods=["DELETE"])
@require_auth_role("admin", "secretaria")
def delete_user(user_id):
    """
    Endpoint per eliminar un usuari

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    {
        "message": "S'ha eliminat l'usuari correctament"
    }
    """
    try:
        db = get_db()
        user = db.query(User).filter(User.id_user == user_id).first()

        if not user:
            return jsonify({"error": "Usuari no trobat"}), 404

        db.delete(user)
        db.commit()

        return jsonify({"message": "S'ha eliminat l'usuari correctament"}), 200

    except ValueError as e:  # pylint: disable=broad-except
        return jsonify({"error": f"Error de validació: {str(e)}"}), 400
    except Exception:  # pylint: disable=broad-except
        return jsonify({"error": "Error intern del servidor"}), 500
