#!/usr/bin/env python3
"""
Script per carregar els usuaris inicials des del fitxer CSV a la base de dades
utilitzant l'endpoint /admin/usuari del servei auth.
"""

from os import path
import csv
import requests
import sys
import time


# Configuració
AUTH_SERVICE_URL = "http://localhost:5002"
ADMIN_LOGIN_ENDPOINT = f"{AUTH_SERVICE_URL}/auth/login"
CREATE_USER_ENDPOINT = f"{AUTH_SERVICE_URL}/admin/usuari"
CSV_USERS_FILE_NAME = "users.csv"

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
    """Crea un usuari mitjançant l'endpoint /admin/usuari."""

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"username": username, "password": password, "role": role}
    try:
        response = requests.post(
            CREATE_USER_ENDPOINT, json=payload, headers=headers, timeout=5
        )
        if response.status_code == 201:
            return True
        elif response.status_code == 409:
            print(f"Ja existeix l'usuari '{username}', s'ha omès.")
            return False
        else:
            print(
                f"Error en crear l'usuari '{username}': {response.status_code} - {response.text}"
            )
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error de connexió en crear l'usuari '{username}': {e}")
        return False


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

                if create_user(token, username, password, role):
                    created += 1
                    # Petit delay per no sobrecarregar el servidor
                    time.sleep(0.1)
                elif "ja existeix" in str(username):
                    skipped += 1
                else:
                    errors += 1

            # Resum
            print("\n" + "-" * 50)
            print(" RESUM DE LA CÀRREGA")
            print("-" * 50)
            print(f" Nombre total d'usuaris al CSV: {total}")
            print(f" Nombre d'usuaris creats: {created}")
            print(f" Nombre d'usuaris saltats: {skipped}")
            print(f" Nombre d'errors: {errors}")
            print("-" * 50)

            return created > 0 or skipped > 0

    except FileNotFoundError:
        print(f"Error: No s'ha trobat el fitxer '{csv_path}'")
        return False
    except Exception as e:
        print(f"Error en llegir el fitxer CSV: {e}")
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

    # Carrega els usuaris del fitxer CSV
    csv_file_path = path.join(dataset_folder, CSV_USERS_FILE_NAME)
    success = load_users_from_csv(csv_file_path, token)
    if success:
        print("\nS'ha completat la càrrega d'usuaris.")
        sys.exit(0)
    else:
        print("\nLa càrrega d'usuaris ha fallat.")
        sys.exit(1)


if __name__ == "__main__":
    main()
