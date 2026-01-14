from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class RoleEnum(enum.Enum):
    admin = "admin"
    metge = "metge"
    secretaria = "secretaria"
    pacient = "pacient"


class User(Base):
    __tablename__ = "users"

    id_user = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)

    def __repr__(self):
        return f"<User(id_user={self.id_user}, username='{self.username}', role='{self.role.value}')>"


class StatusEnum(enum.Enum):
    ACTIU = "ACTIU"
    INACTIU = "INACTIU"


class Patient(Base):
    __tablename__ = "patients"

    id_patient = Column(Integer, primary_key=True, autoincrement=True)
    id_user = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    status = Column(Enum(StatusEnum), nullable=False)

    def __repr__(self):
        return f"<Patient(id_patient={self.id_patient}, name='{self.name}', status='{self.status.value}')>"


class Doctor(Base):
    __tablename__ = "doctors"

    id_doctor = Column(Integer, primary_key=True, autoincrement=True)
    id_user = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Doctor(id_doctor={self.id_doctor}, name='{self.name}', specialty='{self.specialty}')>"


class Center(Base):
    __tablename__ = "centers"

    id_center = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Center(id_center={self.id_center}, name='{self.name}', address='{self.address}')>"
