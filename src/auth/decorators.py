"""Authentication decorators module."""

import os
from functools import wraps

import jwt
from flask import jsonify, request


def require_auth_role(*allowed_roles):
    """
    Decorador que valida el token JWT i verifica el rol de l'usuari.
    Només permet l'accés als usuaris amb els rols especificats.

    Args:
        *allowed_roles: Els rols permesos (ex: 'admin', 'secretaria')

    Returns:
        Decorador que valida el token i el rol
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtenir el token del header Authorization
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                return jsonify({"error": "Missing Authorization header"}), 401

            try:
                # Extreure el token (format: "Bearer <token>")
                parts = auth_header.split()
                if len(parts) != 2 or parts[0].lower() != "bearer":
                    return (
                        jsonify({"error": "Invalid Authorization header format"}),
                        401,
                    )

                token = parts[1]
                SECRET_KEY = os.getenv(
                    "SECRET_KEY", "dev-secret-key-change-in-production"
                )

                # Descodificar el token
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

                # Verificar el rol
                user_role = payload.get("role")
                if user_role not in allowed_roles:
                    return (
                        jsonify(
                            {
                                "error": f"Permís insuficients. Rols necessaris: {', '.join(allowed_roles)}"
                            }
                        ),
                        403,
                    )

                # Passar la informació de l'usuari a la funció
                request.user = payload
                return f(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token ha "}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
            except KeyError as e:  # pylint: disable=broad-except
                return jsonify({"error": f"Invalid token payload: {str(e)}"}), 401
            except Exception:  # pylint: disable=broad-except
                return jsonify({"error": "Authentication failed"}), 401

        return decorated_function

    return decorator
