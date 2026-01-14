#!/usr/bin/env python3
"""
Script per carregar dades (usuaris, pacients, doctors, centres) amb els conjunts
de dades la carpeta dataset utilitzant els endpoints del servei admin.
"""

from os import path
import csv
import requests
import sys
import time


# Configuració
AUTH_SERVICE_URL = "http://localhost:5002"
ADMIN_LOGIN_ENDPOINT = f"{AUTH_SERVICE_URL}/auth/login"
APPOINTMENT_SERVICE_URL = "http://localhost:5001"

# Endpoints admin
CREATE_USER_ENDPOINT = f"{AUTH_SERVICE_URL}/admin/usuari"
CREATE_PATIENT_ENDPOINT = f"{AUTH_SERVICE_URL}/admin/pacients"
CREATE_DOCTOR_ENDPOINT = f"{AUTH_SERVICE_URL}/admin/doctors"
CREATE_CENTER_ENDPOINT = f"{AUTH_SERVICE_URL}/admin/centres"

# Endpoints appointment
CREATE_APPOINTMENT_ENDPOINT = f"{APPOINTMENT_SERVICE_URL}/cites/"

# Fitxers CSV
CSV_USERS_FILE_NAME = "users.csv"
CSV_PATIENTS_FILE_NAME = "patients.csv"
CSV_DOCTORS_FILE_NAME = "doctors.csv"
CSV_CENTERS_FILE_NAME = "centers.csv"
CSV_APPOINTMENTS_FILE_NAME = "appointment.csv"

# Credencials de l'administrador per defecte (per obtenir el token)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


def get_admin_token():
    """Obté el token d'autenticació de l'administrador per defecte."""
    try:
        response = requests.post(
            ADMIN_LOGIN_ENDPOINT,
            json={
                "username": DEFAULT_ADMIN_USERNAME,
                "password": DEFAULT_ADMIN_PASSWORD,
            },
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print("S'ha obtingut el token correctament")
            return token
        else:
            print(
                f"Error en obtenir el token: {response.status_code} - {response.text}"
            )
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error de connexió: {e}")
        return None


def create_user(token, username, password, role):
    """Crea un usuari mitjançant l'endpoint /admin/usuari.

    Retorna: "created" | "exists" | "error".
    """

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"username": username, "password": password, "role": role}
    try:
        response = requests.post(
            CREATE_USER_ENDPOINT, json=payload, headers=headers, timeout=5
        )
        if response.status_code == 201:
            return "created"
        elif response.status_code == 409:
            print(f"Ja existeix l'usuari '{username}', s'ha omès.")
            return "exists"
        else:
            print(
                f"Error en crear l'usuari '{username}': {response.status_code} - {response.text}"
            )
            return "error"

    except requests.exceptions.RequestException as e:
        print(f"Error de connexió en crear l'usuari '{username}': {e}")
        return "error"


def load_users_from_csv(csv_path, token):
    """Llegeix el fitxer CSV i crea els usuaris."""

    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            total = 0
            created = 0
            skipped = 0
            errors = 0

            for row in reader:
                username = row["username"].strip()
                password = row["password"].strip()
                role = row["role"].strip()

                total += 1
                print(f"[{total}] Es crea l'usuari: {username} (rol: {role})")

                # Saltar l'usuari admin per defecte si ja existeix
                if username == DEFAULT_ADMIN_USERNAME:
                    print("S'ha omès l'administrador per defecte")
                    skipped += 1
                    continue

                status = create_user(token, username, password, role)

                if status == "created":
                    created += 1
                    time.sleep(0.05)
                elif status == "exists":
                    skipped += 1
                else:
                    errors += 1
                    print("S'atura la càrrega d'usuaris en trobar el primer error.")
                    return False

            # Resum
            print("\n" + "-" * 50)
            print(" RESUM DE LA CÀRREGA")
            print("-" * 50)
            print(f" Nombre total d'usuaris al CSV: {total}")
            print(f" Nombre d'usuaris creats: {created}")
            print(f" Nombre d'usuaris saltats: {skipped}")
            print(f" Nombre d'errors: {errors}")
            print("-" * 50)
            print("")

            return created > 0 or skipped > 0

    except FileNotFoundError:
        print(f"Error: No s'ha trobat el fitxer '{csv_path}'")
        return False
    except Exception as e:
        print(f"Error en llegir el fitxer CSV: {e}")
        return False


def create_patient(token, id_user, username, password, name, phone, status):
    """Crea un pacient via endpoint /admin/patients.

    Retorna: "created" | "exists" | "error".
    """

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {}
    if id_user:
        payload = {
            "id_user": id_user,
            "name": name,
            "phone": phone,
            "status": status,
        }
    elif username and password:
        payload = {
            "username": username,
            "password": password,
            "name": name,
            "phone": phone,
            "status": status,
        }
    else:
        payload = {
            "name": name,
            "phone": phone,
            "status": status,
        }

    try:
        response = requests.post(
            CREATE_PATIENT_ENDPOINT, json=payload, headers=headers, timeout=5
        )
        if response.status_code == 201:
            return "created"
        elif response.status_code == 409:
            print(f"Ja existeix el pacient '{name}', s'ha omès.")
            return "exists"
        else:
            print(
                f"Error en crear el pacient '{name}': {response.status_code} - {response.text}"
            )
            return "error"
    except requests.exceptions.RequestException as e:
        print(f"Error de connexió en crear el pacient '{name}': {e}")
        return "error"


def load_patients_from_csv(csv_path, token):
    """Carrega pacients des del CSV."""

    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            total = created = skipped = errors = 0

            for row in reader:
                id_user_raw = row.get("id_user", "").strip()
                # id_user és opcional: si és buit o no numèric, es tracta com a None
                id_user = None
                if id_user_raw:
                    try:
                        id_user = int(id_user_raw)
                    except ValueError:
                        print(
                            f"Advertència: id_user no és un enter vàlid ({id_user_raw}), s'ignora"
                        )
                        id_user = None
                username = row.get("username", "").strip()
                password = row.get("password", "").strip()
                name = row.get("name", "").strip()
                phone = row.get("phone", "").strip()
                status = row.get("status", "").strip()

                total += 1
                print(f"[{total}] Es crea el pacient: {name} (id_user: {id_user})")

                if not name or not status:
                    print("Error: manca de dades obligatòries (name/status)")
                    errors += 1
                    return False

                status_create = create_patient(
                    token, id_user, username, password, name, phone or None, status
                )

                if status_create == "created":
                    created += 1
                    time.sleep(0.05)
                elif status_create == "exists":
                    skipped += 1
                else:
                    errors += 1
                    print("S'atura la càrrega de pacients en trobar el primer error.")
                    return False

            print("\n" + "-" * 50)
            print(" RESUM DE PACIENTS")
            print("-" * 50)
            print(f" Total: {total}")
            print(f" Creats: {created}")
            print(f" Omesos: {skipped}")
            print(f" Errors: {errors}")
            print("-" * 50)
            print("")

            return created > 0 or skipped > 0

    except FileNotFoundError:
        print(f"Error: No s'ha trobat el fitxer '{csv_path}'")
        return False
    except Exception as e:
        print(f"Error en llegir el fitxer CSV de pacients: {e}")
        return False


def create_doctor(token, id_user, username, password, name, specialty):
    """Crea un doctor via endpoint /admin/doctors.

    Retorna: "created" | "exists" | "error".
    """

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {}
    if id_user is not None:
        payload = {
            "id_user": id_user,
            "name": name,
            "specialty": specialty,
        }
    elif username and password:
        payload = {
            "username": username,
            "password": password,
            "name": name,
            "specialty": specialty,
        }
    else:
        payload = {
            "name": name,
            "specialty": specialty,
        }

    try:
        response = requests.post(
            CREATE_DOCTOR_ENDPOINT, json=payload, headers=headers, timeout=5
        )
        if response.status_code == 201:
            return "created"
        elif response.status_code == 409:
            print(f"Ja existeix el doctor '{name}', s'ha omès.")
            return "exists"
        else:
            print(
                f"Error en crear el doctor '{name}': {response.status_code} - {response.text}"
            )
            return "error"
    except requests.exceptions.RequestException as e:
        print(f"Error de connexió en crear el doctor '{name}': {e}")
        return "error"


def load_doctors_from_csv(csv_path, token):
    """Carrega doctors des del CSV."""

    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            total = created = skipped = errors = 0

            for row in reader:
                id_user_raw = row.get("id_user", "").strip()
                # id_user és opcional: si és buit o no numèric, es tracta com a None
                id_user = None
                if id_user_raw:
                    try:
                        id_user = int(id_user_raw)
                    except ValueError:
                        print(
                            f"Advertència: id_user no és un enter vàlid ({id_user_raw}), s'ignora"
                        )
                        id_user = None
                username = row.get("username", "").strip()
                password = row.get("password", "").strip()
                name = row.get("name", "").strip()
                specialty = row.get("specialty", "").strip()

                total += 1
                print(f"[{total}] Es crea el doctor: {name} (id_user: {id_user})")

                if not name or not specialty:
                    print("Error: manca de dades obligatòries (name/specialty)")
                    errors += 1
                    return False

                status_create = create_doctor(
                    token, id_user or None, username, password, name, specialty
                )

                if status_create == "created":
                    created += 1
                    time.sleep(0.05)
                elif status_create == "exists":
                    skipped += 1
                else:
                    errors += 1
                    print("S'atura la càrrega de doctors en trobar el primer error.")
                    return False

            print("\n" + "-" * 50)
            print(" RESUM DE DOCTORS")
            print("-" * 50)
            print(f" Total: {total}")
            print(f" Creats: {created}")
            print(f" Omesos: {skipped}")
            print(f" Errors: {errors}")
            print("-" * 50)
            print("")

            return created > 0 or skipped > 0

    except FileNotFoundError:
        print(f"Error: No s'ha trobat el fitxer '{csv_path}'")
        return False
    except Exception as e:
        print(f"Error en llegir el fitxer CSV de doctors: {e}")
        return False


def create_center(token, name, address):
    """Crea un centre via endpoint /admin/centers.

    Retorna: "created" | "exists" | "error".
    """

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"name": name, "address": address}

    try:
        response = requests.post(
            CREATE_CENTER_ENDPOINT, json=payload, headers=headers, timeout=5
        )
        if response.status_code == 201:
            return "created"
        elif response.status_code == 409:
            print(f"Ja existeix el centre '{name}', s'ha omès.")
            return "exists"
        else:
            print(
                f"Error en crear el centre '{name}': {response.status_code} - {response.text}"
            )
            return "error"
    except requests.exceptions.RequestException as e:
        print(f"Error de connexió en crear el centre '{name}': {e}")
        return "error"


def load_centers_from_csv(csv_path, token):
    """Carrega centres des del CSV."""

    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            total = created = skipped = errors = 0

            for row in reader:
                name = row.get("name", "").strip()
                address = row.get("address", "").strip()

                total += 1
                print(f"[{total}] Es crea el centre: {name}")

                if not name or not address:
                    print("Error: manca de dades obligatòries (name/address)")
                    errors += 1
                    return False

                status_create = create_center(token, name, address)

                if status_create == "created":
                    created += 1
                    time.sleep(0.05)
                elif status_create == "exists":
                    skipped += 1
                else:
                    errors += 1
                    print("S'atura la càrrega de centres en trobar el primer error.")
                    return False

            print("\n" + "-" * 50)
            print(" RESUM DE CENTRES")
            print("-" * 50)
            print(f" Total: {total}")
            print(f" Creats: {created}")
            print(f" Omesos: {skipped}")
            print(f" Errors: {errors}")
            print("-" * 50)
            print("")

            return created > 0 or skipped > 0

    except FileNotFoundError:
        print(f"Error: No s'ha trobat el fitxer '{csv_path}'")
        return False
    except Exception as e:
        print(f"Error en llegir el fitxer CSV de centres: {e}")
        return False


def create_appointment(token, date, reason, id_patient, id_doctor, id_center):
    """Crea una cita via endpoint /cites/.

    Retorna: "created" | "exists" | "error".
    """

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "date": date,
        "reason": reason,
        "id_patient": id_patient,
        "id_doctor": id_doctor,
        "id_center": id_center,
    }

    try:
        response = requests.post(
            CREATE_APPOINTMENT_ENDPOINT, json=payload, headers=headers, timeout=5
        )
        if response.status_code == 201:
            return "created"
        elif response.status_code == 409:
            print(
                f"Ja existeix la cita per al pacient {id_patient} a la data {date}, s'ha omès."
            )
            return "exists"
        else:
            print(f"Error en crear la cita: {response.status_code} - {response.text}")
            return "error"
    except requests.exceptions.RequestException as e:
        print(f"Error de connexió en crear la cita: {e}")
        return "error"


def load_appointments_from_csv(csv_path, token):
    """Carrega cites des del CSV."""

    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            total = created = skipped = errors = 0

            for row in reader:
                date = row.get("date", "").strip()
                reason = row.get("reason", "").strip()
                id_patient_raw = row.get("id_patient", "").strip()
                id_doctor_raw = row.get("id_doctor", "").strip()
                id_center_raw = row.get("id_center", "").strip()

                # Convertir ids a enters
                try:
                    id_patient = int(id_patient_raw)
                    id_doctor = int(id_doctor_raw)
                    id_center = int(id_center_raw)
                except ValueError:
                    print(
                        f"Error: ids no vàlids (id_patient: {id_patient_raw}, id_doctor: {id_doctor_raw}, id_center: {id_center_raw})"
                    )
                    errors += 1
                    continue

                total += 1
                print(
                    f"[{total}] Es crea la cita: pacient {id_patient}, doctor {id_doctor}, centre {id_center}, data {date}"
                )

                if (
                    not date
                    or not reason
                    or not id_patient
                    or not id_doctor
                    or not id_center
                ):
                    print("Error: manca de dades obligatòries")
                    errors += 1
                    print("S'atura la càrrega de cites en trobar el primer error.")
                    return False

                status_create = create_appointment(
                    token, date, reason, id_patient, id_doctor, id_center
                )

                if status_create == "created":
                    created += 1
                    time.sleep(0.05)
                elif status_create == "exists":
                    skipped += 1
                else:
                    errors += 1
                    print("S'atura la càrrega de cites en trobar el primer error.")
                    return False

            print("\n" + "-" * 50)
            print(" RESUM DE CITES")
            print("-" * 50)
            print(f" Total: {total}")
            print(f" Creats: {created}")
            print(f" Omesos: {skipped}")
            print(f" Errors: {errors}")
            print("-" * 50)
            print("")

            return created > 0 or skipped > 0

    except FileNotFoundError:
        print(f"Error: No s'ha trobat el fitxer '{csv_path}'")
        return False
    except Exception as e:
        print(f"Error en llegir el fitxer CSV de cites: {e}")
        return False


def main():
    """Funció principal."""

    # Defineix el camí a la carpeta dataset
    dataset_folder = path.join(path.dirname(path.dirname(__file__)), "dataset")

    # Obté el token de l'administrador per defecte
    token = get_admin_token()

    if not token:
        print("\nNo s'ha pogut obtenir el token de l'administrador per defecte.")
        print(
            "Assegura't que el servei auth està en execució i que l'administrador per defecte està creat."
        )
        sys.exit(1)

    # Carrega usuaris
    csv_users = path.join(dataset_folder, CSV_USERS_FILE_NAME)
    users_ok = load_users_from_csv(csv_users, token)
    if users_ok == False:
        print("La càrrega de dades ha finalitzat amb errors o omissions.")
        sys.exit(1)

    # Carrega pacients
    csv_patients = path.join(dataset_folder, CSV_PATIENTS_FILE_NAME)
    patients_ok = load_patients_from_csv(csv_patients, token)
    if patients_ok == False:
        print("La càrrega de dades ha finalitzat amb errors o omissions.")
        sys.exit(1)

    # Carrega doctors
    csv_doctors = path.join(dataset_folder, CSV_DOCTORS_FILE_NAME)
    doctors_ok = load_doctors_from_csv(csv_doctors, token)
    if doctors_ok == False:
        print("La càrrega de dades ha finalitzat amb errors o omissions.")
        sys.exit(1)

    # Carrega centres
    csv_centers = path.join(dataset_folder, CSV_CENTERS_FILE_NAME)
    centers_ok = load_centers_from_csv(csv_centers, token)
    if centers_ok == False:
        print("La càrrega de dades ha finalitzat amb errors o omissions.")
        sys.exit(1)

    # Carrega cites
    csv_appointments = path.join(dataset_folder, CSV_APPOINTMENTS_FILE_NAME)
    appointments_ok = load_appointments_from_csv(csv_appointments, token)
    if appointments_ok == False:
        print("La càrrega de dades ha finalitzat amb errors o omissions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
