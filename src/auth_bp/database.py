import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from werkzeug.security import generate_password_hash
from models import Base, User, RolEnum

# Configuració de la base de dades
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/auth.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Crear engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True,  # Canvia a False en producció
)

# Crear session factory
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


def init_db():
    """Inicialitza la base de dades creant totes les taules"""
    Base.metadata.create_all(bind=engine)


def create_default_admin():
    """Crea l'usuari administrador per defecte si no existeix cap usuari"""
    db = SessionLocal()
    try:
        # Verificar si ja hi ha usuaris a la base de dades
        user_count = db.query(User).count()

        if user_count == 0:
            # Obtenir dades de les variables d'entorn
            admin_username = os.getenv("DEFAULT_ADMIN_USER", "admin")
            admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
            admin_role = os.getenv("DEFAULT_ADMIN_ROLE", "admin")

            # Validar que el rol sigui vàlid
            try:
                role_enum = RolEnum[admin_role]
            except KeyError:
                print(f"Rol '{admin_role}' no vàlid. Utilitzant 'admin' per defecte.")
                role_enum = RolEnum.admin

            # Crear l'usuari administrador
            admin_user = User(
                username=admin_username,
                password=generate_password_hash(admin_password),
                rol=role_enum,
            )

            db.add(admin_user)
            db.commit()
            print(
                f"Usuari administrador '{admin_username}' creat correctament amb rol '{role_enum.value}'."
            )
        else:
            print(
                f"La base de dades ja conté {user_count} usuari(s). No es crea l'usuari per defecte."
            )

    except Exception as e:
        db.rollback()
        print(f"Error creant l'usuari administrador per defecte: {e}")
    finally:
        db.close()


def get_db():
    """Retorna una sessió de base de dades"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
