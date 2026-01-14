"""Mòdul d'administració amb els endpoints per a la gestió d'usuaris, pacients, doctors i centres."""

from flask import Blueprint, request, jsonify
from database import SessionLocal, get_db
from models import Patient, Doctor, Center, StatusEnum, User, RoleEnum
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
from decorators import require_auth_role

admin_bp = Blueprint("admin", __name__)


# ENDPOINTS DELS USUARIS =======================================================


@admin_bp.route("/usuari", methods=["GET"])
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


@admin_bp.route("/usuari/<int:user_id>", methods=["GET"])
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

        # Comprovar si l'usuari existeix
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

    except ValueError as e:
        return jsonify({"error": f"Error de validació: {str(e)}"}), 400
    except Exception:
        return jsonify({"error": "Error intern del servidor"}), 500


@admin_bp.route("/usuari", methods=["POST"])
@require_auth_role("admin")
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
        "role": "admin|secretaria"
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

        # Comprovar camps obligatoris
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

        # Validar que el rol sigui vàlid: admin o secretaria
        valid_roles = ["admin", "secretaria"]
        if role not in valid_roles:
            return (
                jsonify(
                    {
                        "error": f"Rol invàlid. Ha de ser un de: {', '.join([r.value for r in RoleEnum])}"
                    }
                ),
                400,
            )

        # Verifica que l'usuari no existeixi
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
            role=RoleEnum[role],
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

    except ValueError as e:
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception:
        return jsonify({"error": "Internal server error"}), 500


@admin_bp.route("/usuari/<int:user_id>", methods=["PUT"])
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

        # Comprovar si l'usuari existeix
        if not user:
            return jsonify({"error": "Usuari no trobat"}), 404

        # Verifica que una secretaria no pugui modificar usuaris admin
        current_user_role = request.user.get("role")
        if current_user_role == "secretaria" and user.role == RoleEnum.admin:
            return (
                jsonify(
                    {
                        "error": "Una secretaria no pot modificar els usuaris amb rol admin"
                    }
                ),
                403,
            )

        data = request.get_json()

        if not data:
            return jsonify({"error": "No s'ha proporcionat cap dada"}), 400

        # Actualitzar username si es proporciona
        if "username" in data:
            username = data["username"]

            # Verifica que el nou username no existeixi
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

                # Verifica que una secretaria no pugui assignar rol admin
                if current_user_role == "secretaria" and role_enum == RoleEnum.admin:
                    return (
                        jsonify(
                            {"error": "Una secretaria no pot assignar el rol admin"}
                        ),
                        403,
                    )

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

    except ValueError as e:
        return jsonify({"error": f"Error de validació: {str(e)}"}), 400
    except Exception:
        return jsonify({"error": "Error intern del servidor"}), 500


@admin_bp.route("/usuari/<int:user_id>", methods=["DELETE"])
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
        # Comprovar si l'usuari existeix
        if not user:
            return jsonify({"error": "Usuari no trobat"}), 404

        # Verifica que una secretaria no pugui eliminar usuaris admin
        current_user_role = request.user.get("role")
        if current_user_role == "secretaria" and user.role == RoleEnum.admin:
            return (
                jsonify(
                    {"error": "Una secretaria no pot eliminar usuaris amb rol admin"}
                ),
                403,
            )

        db.delete(user)
        db.commit()

        return jsonify({"message": "S'ha eliminat l'usuari correctament"}), 200

    except ValueError as e:
        return jsonify({"error": f"Error de validació: {str(e)}"}), 400
    except Exception:
        return jsonify({"error": "Error intern del servidor"}), 500


# ENDPOINTS DELS PACIENTS ======================================================


@admin_bp.route("/pacients", methods=["GET"])
@require_auth_role("admin", "secretaria")
def get_patients():
    """
    Endpoint per obtenir tots els pacients

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    [
        {
            "id_patient": int,
            "id_user": int,
            "name": "string",
            "phone": "string",
            "status": "ACTIU|INACTIU"
        },
        ...
    ]
    """
    db: Session = SessionLocal()
    try:
        patients = db.query(Patient).all()
        return (
            jsonify(
                [
                    {
                        "id_patient": p.id_patient,
                        "id_user": p.id_user,
                        "name": p.name,
                        "phone": p.phone,
                        "status": p.status.value,
                    }
                    for p in patients
                ]
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/pacients/<int:id_patient>", methods=["GET"])
@require_auth_role("admin", "pacient")
def get_patient(id_patient):
    """
    Endpoint per obtenir un pacient amb l'ID

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    {
        "id_patient": int,
        "id_user": int,
        "name": "string",
        "phone": "string",
        "status": "ACTIU|INACTIU"
    }
    """
    db: Session = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id_patient == id_patient).first()
        # Comprovar si el pacient existeix
        if not patient:
            return jsonify({"error": "No s'ha trobat el pacient"}), 404

        return (
            jsonify(
                {
                    "id_patient": patient.id_patient,
                    "id_user": patient.id_user,
                    "name": patient.name,
                    "phone": patient.phone,
                    "status": patient.status.value,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/pacients", methods=["POST"])
@require_auth_role("admin")
def create_patient():
    """
    Endpoint per crear un nou pacient

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Petició JSON:
    {
        "id_user": int (opcional),
        "username": "string" (opcional),
        "password": "string" (opcional),
        "name": "string",
        "phone": "string" (opcional),
        "status": "ACTIU|INACTIU"
    }

    Resposta JSON:
    {
        "id_patient": int,
        "id_user": int,
        "name": "string",
        "phone": "string",
        "status": "ACTIU|INACTIU"
    }
    """
    db: Session = SessionLocal()
    try:
        data = request.get_json()

        # Comprovar camps obligatoris
        if not data or "name" not in data or "status" not in data:
            return (
                jsonify({"error": "Els camps 'name' i 'status' són obligatoris"}),
                400,
            )

        # Validar l'estat
        try:
            status_enum = StatusEnum[data["status"]]
        except KeyError:
            return (
                jsonify({"error": "L'estat no és vàlid. Utilitza 'ACTIU' o 'INACTIU'"}),
                400,
            )

        # Comprovar si ja existeix un pacient amb el mateix id_user
        id_user = data.get("id_user")
        username = data.get("username")
        password = data.get("password")
        if id_user is not None:
            # Comprovar que no es proporcionin username o password juntament amb id_user
            if username is not None or password is not None:
                return (
                    jsonify(
                        {
                            "error": "No es pot proporcionar id_user juntament amb username o password"
                        }
                    ),
                    400,
                )
            # Comprovar si ja existeix un pacient amb el mateix id_user
            existing_patient = (
                db.query(Patient).filter(Patient.id_user == id_user).first()
            )
            if existing_patient:
                return (
                    jsonify({"error": f"Ja existeix un pacient amb id_user {id_user}"}),
                    409,
                )
        else:
            if username and password:
                # Comprovar si ja existeix un usuari amb el mateix username
                existing_user = db.query(User).filter(User.username == username).first()
                if existing_user:
                    return (
                        jsonify(
                            {"error": f"Ja existeix un usuari amb username {username}"}
                        ),
                        409,
                    )
                # Crear l'usuari associat
                new_user = User(
                    username=username,
                    password=generate_password_hash(password),
                    role=RoleEnum.pacient,
                )
                db.add(new_user)
                db.commit()
                id_user = new_user.id_user

        new_patient = Patient(
            id_user=id_user,
            name=data["name"],
            phone=data.get("phone"),
            status=status_enum,
        )

        db.add(new_patient)
        db.commit()

        return (
            jsonify(
                {
                    "id_patient": new_patient.id_patient,
                    "id_user": new_patient.id_user,
                    "name": new_patient.name,
                    "phone": new_patient.phone,
                    "status": new_patient.status.value,
                }
            ),
            201,
        )
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Error d'integritat en la base de dades"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/pacients/<int:id_patient>", methods=["PUT"])
@require_auth_role("admin", "secretaria")
def update_patient(id_patient):
    """
    Endpoint per actualitzar un pacient

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Petició JSON:
    {
        "id_user": int (opcional),
        "name": "string" (opcional),
        "phone": "string" (opcional),
        "status": "ACTIU|INACTIU" (opcional)
    }

    Resposta JSON:
    {
        "id_patient": int,
        "id_user": int,
        "name": "string",
        "phone": "string",
        "status": "ACTIU|INACTIU"
    }
    """
    db: Session = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id_patient == id_patient).first()
        # Comprovar si el pacient existeix
        if not patient:
            return jsonify({"error": "No s'ha trobat el pacient"}), 404

        data = request.get_json()

        if "name" in data:
            patient.name = data["name"]
        if "phone" in data:
            patient.phone = data["phone"]
        if "status" in data:
            try:
                patient.status = StatusEnum[data["status"]]
            except KeyError:
                return (
                    jsonify(
                        {"error": "L'estat no és vàlid. Utilitza 'ACTIU' o 'INACTIU'"}
                    ),
                    400,
                )
        if "id_user" in data:
            patient.id_user = data["id_user"]

        db.commit()

        return (
            jsonify(
                {
                    "id_patient": patient.id_patient,
                    "id_user": patient.id_user,
                    "name": patient.name,
                    "phone": patient.phone,
                    "status": patient.status.value,
                }
            ),
            200,
        )
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/pacients/<int:id_patient>", methods=["DELETE"])
@require_auth_role("admin", "secretaria")
def delete_patient(id_patient):
    """
    Endpoint per eliminar un pacient

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    {
        "message": "S'ha eliminat correctament el pacient"
    }
    """
    db: Session = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id_patient == id_patient).first()
        # Comprovar si el pacient existeix
        if not patient:
            return jsonify({"error": "No s'ha trobat el pacient"}), 404

        # Elimina l'usuari associat si existeix del pacient
        if patient.id_user:
            user = db.query(User).filter(User.id_user == patient.id_user).first()
            if user:
                db.delete(user)

        db.delete(patient)
        db.commit()

        return jsonify({"message": "S'ha eliminat correctament el pacient"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ENDPOINTS DELS DOCTORS =======================================================


@admin_bp.route("/doctors", methods=["GET"])
@require_auth_role("admin", "secretaria")
def get_doctors():
    """
    Endpoint per obtenir tots els doctors

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    [
        {
            "id_doctor": int,
            "id_user": int,
            "name": "string",
            "specialty": "string"
        },
        ...
    ]
    """
    db: Session = SessionLocal()
    try:
        doctors = db.query(Doctor).all()
        return (
            jsonify(
                [
                    {
                        "id_doctor": d.id_doctor,
                        "id_user": d.id_user,
                        "name": d.name,
                        "specialty": d.specialty,
                    }
                    for d in doctors
                ]
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/doctors/<int:id_doctor>", methods=["GET"])
@require_auth_role("admin", "pacient")
def get_doctor(id_doctor):
    """
    Endpoint per obtenir un doctor amb l'ID

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    {
        "id_doctor": int,
        "id_user": int,
        "name": "string",
        "specialty": "string"
    }
    """
    db: Session = SessionLocal()
    try:
        doctor = db.query(Doctor).filter(Doctor.id_doctor == id_doctor).first()
        # Comprovar si el doctor existeix
        if not doctor:
            return jsonify({"error": "No s'ha trobat el doctor"}), 404

        return (
            jsonify(
                {
                    "id_doctor": doctor.id_doctor,
                    "id_user": doctor.id_user,
                    "name": doctor.name,
                    "specialty": doctor.specialty,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/doctors", methods=["POST"])
@require_auth_role("admin")
def create_doctor():
    """
    Endpoint per crear un nou doctor

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Petició JSON:
    {
        "id_user": int (opcional),
        "username": "string" (opcional),
        "password": "string" (opcional),
        "name": "string",
        "specialty": "string"
    }

    Resposta JSON:
    {
        "id_doctor": int,
        "id_user": int,
        "name": "string",
        "specialty": "string"
    }
    """
    db: Session = SessionLocal()
    try:
        data = request.get_json()

        # Comprovar camps obligatoris
        if not data or "name" not in data or "specialty" not in data:
            return (
                jsonify({"error": "Els camps 'name' i 'specialty' són obligatoris"}),
                400,
            )

        # Comprovar si ja existeix un doctor amb el mateix id_user
        id_user = data.get("id_user")
        username = data.get("username")
        password = data.get("password")
        if id_user is not None:
            # Comprovar que no es proporcionin username o password juntament amb id_user
            if username is not None or password is not None:
                return (
                    jsonify(
                        {
                            "error": "No es pot proporcionar id_user juntament amb username o password"
                        }
                    ),
                    400,
                )
            # Comprovar si ja existeix un doctor amb el mateix id_user
            existing_doctor = db.query(Doctor).filter(Doctor.id_user == id_user).first()
            if existing_doctor:
                return (
                    jsonify({"error": f"Ja existeix un doctor amb id_user {id_user}"}),
                    409,
                )
        else:
            # Crear usuari associat si es proporcionen username i password
            if username and password:
                # Comprovar si ja existeix un usuari amb el mateix username
                existing_user = db.query(User).filter(User.username == username).first()
                if existing_user:
                    return (
                        jsonify(
                            {"error": f"Ja existeix un usuari amb username {username}"}
                        ),
                        409,
                    )
                # Crear l'usuari associat
                new_user = User(
                    username=username,
                    password=generate_password_hash(password),
                    role=RoleEnum.metge,
                )
                db.add(new_user)
                db.commit()
                id_user = new_user.id_user

        new_doctor = Doctor(
            id_user=id_user, name=data["name"], specialty=data["specialty"]
        )

        db.add(new_doctor)
        db.commit()

        return (
            jsonify(
                {
                    "id_doctor": new_doctor.id_doctor,
                    "id_user": new_doctor.id_user,
                    "name": new_doctor.name,
                    "specialty": new_doctor.specialty,
                }
            ),
            201,
        )
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Error d'integritat en la base de dades"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/doctors/<int:id_doctor>", methods=["PUT"])
@require_auth_role("admin", "secretaria")
def update_doctor(id_doctor):
    """
    Endpoint per actualitzar un doctor

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Petició JSON:
    {
        "id_user": int (opcional),
        "name": "string" (opcional),
        "specialty": "string" (opcional)
    }

    Resposta JSON:
    {
        "id_doctor": int,
        "id_user": int,
        "name": "string",
        "specialty": "string"
    }
    """
    db: Session = SessionLocal()
    try:
        doctor = db.query(Doctor).filter(Doctor.id_doctor == id_doctor).first()
        # Comprovar si el doctor existeix
        if not doctor:
            return jsonify({"error": "No s'ha trobat el doctor"}), 404

        data = request.get_json()

        if "name" in data:
            doctor.name = data["name"]
        if "specialty" in data:
            doctor.specialty = data["specialty"]
        if "id_user" in data:
            doctor.id_user = data["id_user"]

        db.commit()

        return (
            jsonify(
                {
                    "id_doctor": doctor.id_doctor,
                    "id_user": doctor.id_user,
                    "name": doctor.name,
                    "specialty": doctor.specialty,
                }
            ),
            200,
        )
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/doctors/<int:id_doctor>", methods=["DELETE"])
@require_auth_role("admin", "secretaria")
def delete_doctor(id_doctor):
    """
    Endpoint per eliminar un doctor

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    {
        "message": "S'ha eliminat correctament el doctor"
    }
    """
    db: Session = SessionLocal()
    try:
        doctor = db.query(Doctor).filter(Doctor.id_doctor == id_doctor).first()
        # Comprovar si el doctor existeix
        if not doctor:
            return jsonify({"error": "No s'ha trobat el doctor"}), 404

        # Elimina l'usuari associat si existeix del doctor
        if doctor.id_user:
            user = db.query(User).filter(User.id_user == doctor.id_user).first()
            if user:
                db.delete(user)

        db.delete(doctor)
        db.commit()

        return jsonify({"message": "S'ha eliminat correctament el doctor"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ENDPOINTS DELS CENTRES =======================================================


@admin_bp.route("/centres", methods=["GET"])
@require_auth_role("admin", "secretaria")
def get_centers():
    """
    Endpoint per obtenir tots els centres

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    [
        {
            "id_center": int,
            "name": "string",
            "address": "string"
        },
        ...
    ]
    """
    db: Session = SessionLocal()
    try:
        centers = db.query(Center).all()
        return (
            jsonify(
                [
                    {"id_center": c.id_center, "name": c.name, "address": c.address}
                    for c in centers
                ]
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/centres/<int:id_center>", methods=["GET"])
@require_auth_role("admin", "pacient")
def get_center(id_center):
    """
    Endpoint per obtenir un centre per ID

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    {
        "id_center": int,
        "name": "string",
        "address": "string"
    }
    """
    db: Session = SessionLocal()
    try:
        center = db.query(Center).filter(Center.id_center == id_center).first()
        # Comprovar si el centre existeix
        if not center:
            return jsonify({"error": "No s'ha trobat el centre"}), 404

        return (
            jsonify(
                {
                    "id_center": center.id_center,
                    "name": center.name,
                    "address": center.address,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/centres", methods=["POST"])
@require_auth_role("admin")
def create_center():
    """
    Endpoint per crear un nou centre

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Petició JSON:
    {
        "name": "string",
        "address": "string"
    }

    Resposta JSON:
    {
        "id_center": int,
        "name": "string",
        "address": "string"
    }
    """
    db: Session = SessionLocal()
    try:
        data = request.get_json()

        # Comprovar camps obligatoris
        if not data or "name" not in data or "address" not in data:
            return (
                jsonify({"error": "Els camps 'name' i 'address' són obligatoris"}),
                400,
            )

        # Comprovar si ja existeix un centre amb el mateix nom i adreça
        name = data["name"]
        address = data["address"]
        existing_center = (
            db.query(Center)
            .filter(Center.name == name, Center.address == address)
            .first()
        )
        if existing_center:
            return (
                jsonify(
                    {
                        "error": f"Ja existeix un centre amb nom '{name}' i adreça '{address}'"
                    }
                ),
                409,
            )

        new_center = Center(name=name, address=address)

        db.add(new_center)
        db.commit()

        return (
            jsonify(
                {
                    "id_center": new_center.id_center,
                    "name": new_center.name,
                    "address": new_center.address,
                }
            ),
            201,
        )
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Error d'integritat en la base de dades"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/centres/<int:id_center>", methods=["PUT"])
@require_auth_role("admin", "secretaria")
def update_center(id_center):
    """
    Endpoint per actualitzar un centre

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Petició JSON:
    {
        "name": "string" (opcional),
        "address": "string" (opcional)
    }

    Resposta JSON:
    {
        "id_center": int,
        "name": "string",
        "address": "string"
    }
    """
    db: Session = SessionLocal()
    try:
        center = db.query(Center).filter(Center.id_center == id_center).first()
        # Comprovar si el centre existeix
        if not center:
            return jsonify({"error": "No s'ha trobat el centre"}), 404

        data = request.get_json()

        if "name" in data:
            center.name = data["name"]
        if "address" in data:
            center.address = data["address"]

        db.commit()

        return (
            jsonify(
                {
                    "id_center": center.id_center,
                    "name": center.name,
                    "address": center.address,
                }
            ),
            200,
        )
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@admin_bp.route("/centres/<int:id_center>", methods=["DELETE"])
@require_auth_role("admin", "secretaria")
def delete_center(id_center):
    """
    Endpoint per eliminar un centre

    Capçaleres:
    {
        "Authorization": "Bearer <token>"
    }

    Resposta JSON:
    {
        "message": "S'ha eliminat correctament el centre"
    }
    """
    db: Session = SessionLocal()
    try:
        center = db.query(Center).filter(Center.id_center == id_center).first()
        # Comprovar si el centre existeix
        if not center:
            return jsonify({"error": "No s'ha trobat el centre"}), 404

        db.delete(center)
        db.commit()

        return jsonify({"message": "S'ha eliminat correctament el centre"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
