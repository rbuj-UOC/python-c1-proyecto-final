import datetime
import os

import jwt

from flask import Blueprint, request, jsonify
import requests
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Appointment, AppointmentStatusEnum
from decorators import require_auth_role

cites_bp = Blueprint("cites", __name__)


def parse_datetime(value: str):
    """Parses ISO-8601 datetime strings; returns datetime or None."""
    try:
        return datetime.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def serialize(appointment: Appointment):
    return {
        "id_appointment": appointment.id_appointment,
        "date": appointment.date.isoformat(),
        "reason": appointment.reason,
        "status": appointment.status.value,
        "id_patient": appointment.id_patient,
        "id_doctor": appointment.id_doctor,
        "id_center": appointment.id_center,
        "id_user_register": appointment.id_user_register,
    }


@cites_bp.route("/", methods=["GET"])
@require_auth_role("admin", "metge", "secretaria")
def list_appointments():
    """
    Endpoint per llistar totes les cites.

    Capçaleres:
    {
        Authorization: Bearer <token>
    }

    Resposta JSON:
    [
        {
            "id_appointment": int,
            "date": "2024-07-01T10:00:00",
            "reason": "Consulta general",
            "status": "ACTIVE",
            "id_patient": 1,
            "id_doctor": 2,
            "id_center": 1,
            "id_user_register": 3
        },
        ...
    ]
    """
    # Obté el rol de l'usuari amb el token incrustat a la capçalera
    auth_header = request.headers.get("Authorization")
    parts = auth_header.split()
    token = parts[1]
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user_role = payload.get("role")

    if user_role == "metge":
        # Filtra per paràmetres opcionals
        db: Session = SessionLocal()
        query = db.query(Appointment)
        # Filtra amb l'identificador del doctor si s'ha passat en la consulta
        id_doctor = request.args.get("id_doctor")
        if id_doctor:
            query = query.filter(Appointment.id_doctor == id_doctor)
        else:
            return (
                jsonify(
                    {"error": "el paràmetre id_doctor és obligatori per als doctors"}
                ),
                400,
            )
        # Executa la consulta
        try:
            items = query.all()
            return jsonify([serialize(a) for a in items]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    elif user_role == "secretaria":
        # Filtra per paràmetres opcionals
        db: Session = SessionLocal()
        query = db.query(Appointment)
        # Filtra per rang de dates si s'han passat en la consulta
        date_from = request.args.get("date_from")
        if date_from:
            dt_from = parse_datetime(date_from)
            if dt_from is None:
                return jsonify({"error": "Invalid date_from format"}), 400
            query = query.filter(Appointment.date >= dt_from)
        date_to = request.args.get("date_to")
        if date_to:
            dt_to = parse_datetime(date_to)
            if dt_to is None:
                return jsonify({"error": "Invalid date_to format"}), 400
            query = query.filter(Appointment.date <= dt_to)
        # Executa la consulta
        try:
            items = query.all()
            return jsonify([serialize(a) for a in items]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    else:
        # Filtra per paràmetres opcionals
        db: Session = SessionLocal()
        query = db.query(Appointment)
        # Filtra amb l'identificador del doctor si s'ha passat en la consulta
        id_doctor = request.args.get("id_doctor")
        if id_doctor:
            query = query.filter(Appointment.id_doctor == id_doctor)
        # Filtra amb l'identificador del centre si s'ha passat en la consulta
        id_center = request.args.get("id_center")
        if id_center:
            query = query.filter(Appointment.id_center == id_center)
        # Filtra amb l'estat si s'ha passat en la consulta
        status = request.args.get("status")
        if status:
            try:
                status_enum = AppointmentStatusEnum[status]
                query = query.filter(Appointment.status == status_enum)
            except KeyError:
                return jsonify({"error": "Invalid status value"}), 400
        # Filtra per rang de dates si s'han passat en la consulta
        date_from = request.args.get("date_from")
        if date_from:
            dt_from = parse_datetime(date_from)
            if dt_from is None:
                return jsonify({"error": "Invalid date_from format"}), 400
            query = query.filter(Appointment.date >= dt_from)
        date_to = request.args.get("date_to")
        if date_to:
            dt_to = parse_datetime(date_to)
            if dt_to is None:
                return jsonify({"error": "Invalid date_to format"}), 400
            query = query.filter(Appointment.date <= dt_to)
        # Filtra amb l'identificador del pacient si s'ha passat en la consulta
        id_patient = request.args.get("id_patient")
        if id_patient:
            query = query.filter(Appointment.id_patient == id_patient)
        # Executa la consulta
        try:
            items = query.all()
            return jsonify([serialize(a) for a in items]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()


@cites_bp.route("/", methods=["POST"])
@require_auth_role("admin", "pacient")
def create_appointment():
    """
    Endpoint per crear una nova cita.

    Capçaleres:
    {
        Authorization: Bearer <token>
    }

    Petició JSON:
    {
        "date": "2026-07-01T10:00:00",
        "reason": "Consulta general",
        "id_patient": 1,
        "id_doctor": 2,
        "id_center": 1,
    }

    Resposta JSON:
    {
        "id_appointment": int,
        "date": "2026-07-01T10:00:00",
        "reason": "Consulta general",
        "status": "ACTIVE",
        "id_patient": 1,
        "id_doctor": 2,
        "id_center": 1,
        "id_user_register": 3
    }
    """
    db: Session = SessionLocal()
    try:
        data = request.get_json() or {}

        required_fields = [
            "date",
            "reason",
            "id_patient",
            "id_doctor",
            "id_center",
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return (
                jsonify({"error": f"Falten camps obligatoris: {', '.join(missing)}"}),
                400,
            )

        # Obté el payload del token
        auth_header = request.headers.get("Authorization")
        parts = auth_header.split()
        token = parts[1]
        SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        dt = parse_datetime(data.get("date"))
        if dt is None:
            return (
                jsonify({"error": "El camp 'date' ha de tenir el format ISO-8601"}),
                400,
            )

        ADMIN_HOST = os.getenv("ADMIN_HOST", "localhost")
        ADMIN_PORT = os.getenv("ADMIN_PORT", "5002")
        # Comprovar que el pacient existeix
        try:
            admin_url = f"http://{ADMIN_HOST}:{ADMIN_PORT}/admin/pacients/{data.get('id_patient')}"
            # afegeix el token d'autenticació
            resp = requests.get(
                admin_url, headers={"Authorization": auth_header}, timeout=5
            )
            print(resp.status_code)
            if resp.status_code != 200:
                return jsonify({"error": "El pacient no existeix"}), 400
        except Exception:
            return jsonify({"error": "No s'ha pogut verificar el pacient"}), 500

        # Comprovar que el doctor existeix
        try:
            admin_url = f"http://{ADMIN_HOST}:{ADMIN_PORT}/admin/doctors/{data.get('id_doctor')}"
            resp = requests.get(
                admin_url, headers={"Authorization": auth_header}, timeout=5
            )
            if resp.status_code != 200:
                return jsonify({"error": "El doctor no existeix"}), 400
        except Exception:
            return jsonify({"error": "No s'ha pogut verificar el doctor"}), 500

        # Comprovar que el centre existeix
        try:
            admin_url = f"http://{ADMIN_HOST}:{ADMIN_PORT}/admin/centres/{data.get('id_center')}"
            resp = requests.get(
                admin_url, headers={"Authorization": auth_header}, timeout=5
            )
            if resp.status_code != 200:
                return jsonify({"error": "El centre no existeix"}), 400
        except Exception:
            return jsonify({"error": "No s'ha pogut verificar el centre"}), 500

        # Comprovar que no hi ha cites conflictives (mateix doctor i centre dins de 30 minuts)
        time_buffer = datetime.timedelta(minutes=30)
        start_time = dt - time_buffer
        end_time = dt + time_buffer

        conflicting_appointments = (
            db.query(Appointment)
            .filter(
                Appointment.id_doctor == data.get("id_doctor"),
                Appointment.id_center == data.get("id_center"),
                Appointment.status == AppointmentStatusEnum.ACTIVE,
                Appointment.date >= start_time,
                Appointment.date <= end_time,
            )
            .all()
        )

        if conflicting_appointments:
            return (
                jsonify(
                    {
                        "error": "No es pot programar una cita per aquest doctor i centre. Hi ha una cita conflictiva dins de 30 minuts abans o després."
                    }
                ),
                409,
            )

        appointment = Appointment(
            date=dt,
            reason=data.get("reason"),
            status=AppointmentStatusEnum["ACTIVE"],
            id_patient=data.get("id_patient"),
            id_doctor=data.get("id_doctor"),
            id_center=data.get("id_center"),
            id_user_register=payload.get("id_user"),
        )

        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return jsonify(serialize(appointment)), 201
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Error d'integritat en la base de dades"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@cites_bp.route("/<int:id_appointment>", methods=["PUT"])
@require_auth_role("admin", "secretaria")
def cancel_appointment(id_appointment):
    """
    Endpoint per cancel·lar una cita existent.

    Capçaleres:
    {
        Authorization: Bearer <token>
    }

    Resposta JSON:
    {
        "message": "La cita ha estat cancel·lada"
    }
    """
    db: Session = SessionLocal()
    try:
        a = (
            db.query(Appointment)
            .filter(Appointment.id_appointment == id_appointment)
            .first()
        )
        if not a:
            return jsonify({"error": "No s'ha trobat la cita"}), 404

        if a.status == AppointmentStatusEnum.CANCELLED:
            return jsonify({"error": "La cita ja està cancel·lada"}), 400
        a.status = AppointmentStatusEnum.CANCELLED

        db.commit()
        db.refresh(a)
        return jsonify({"message": "La cita ha estat cancel·lada"}), 200
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Error d'integritat en la base de dades"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@cites_bp.route("/<int:id_appointment>", methods=["DELETE"])
@require_auth_role("admin", "secretaria")
def delete_appointment(id_appointment):
    """
    Endpoint per eliminar una cita existent.

    Capçaleres:
    {
        Authorization: Bearer <token>
    }
    Resposta JSON:
    {
        "message": "S'ha eliminat la cita"
    }
    """
    db: Session = SessionLocal()
    try:
        a = (
            db.query(Appointment)
            .filter(Appointment.id_appointment == id_appointment)
            .first()
        )
        if not a:
            return jsonify({"error": "No s'ha trobat la cita"}), 404

        db.delete(a)
        db.commit()
        return jsonify({"message": "S'ha eliminat la cita"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
