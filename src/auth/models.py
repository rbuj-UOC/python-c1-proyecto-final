from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class RolEnum(enum.Enum):
    admin = "admin"
    metge = "metge"
    secretaria = "secretaria"
    pacient = "pacient"


class User(Base):
    __tablename__ = "users"

    id_user = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(Enum(RolEnum), nullable=False)

    def __repr__(self):
        return f"<User(id_user={self.id_user}, username='{self.username}', rol='{self.rol.value}')>"
