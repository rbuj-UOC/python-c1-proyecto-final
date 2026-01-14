from sqlalchemy import Column, Integer, String, Enum
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
