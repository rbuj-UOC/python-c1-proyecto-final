from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class AppointmentStatusEnum(enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


class Appointment(Base):
    __tablename__ = "appointments"

    id_appointment = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(Enum(AppointmentStatusEnum), nullable=False)
    id_patient = Column(Integer, nullable=False)
    id_doctor = Column(Integer, nullable=False)
    id_center = Column(Integer, nullable=False)
    id_user_register = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Appointment(id_cita={self.id_cita}, data='{self.data}', status='{self.status.value}')>"
