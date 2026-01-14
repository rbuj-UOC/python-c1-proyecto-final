import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base

# Configuració de la base de dades
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/appointments.db")
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
    """Inicialitza la base de dades creant totes les taules."""
    Base.metadata.create_all(bind=engine)
