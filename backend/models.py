from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from database import Base
import enum


class UserRole(str, enum.Enum):
    LEGAL_PROFESSIONAL = "legal_professional"
    COURT_ADMIN = "court_admin"
    SUPERADMIN = "superadmin"


class ScraperStatus(str, enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    RUNNING = "running"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.LEGAL_PROFESSIONAL, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class Cause(Base):
    __tablename__ = "causes"

    id = Column(Integer, primary_key=True, index=True)
    sr_no = Column(String(50), index=True)
    court_no = Column(String(50), index=True)
    case_no = Column(String(100), index=True)
    petitioner = Column(Text)
    respondent = Column(Text)
    advocate = Column(String(255), index=True)
    hearing_date = Column(Date, index=True)
    hearing_time = Column(Time)
    case_type = Column(String(100), index=True)
    raw_text = Column(Text)
    is_hrce = Column(Boolean, default=False, index=True)
    inserted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ScraperLog(Base):
    __tablename__ = "scraper_logs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(ScraperStatus), nullable=False)
    records_extracted = Column(Integer, default=0)
    error_message = Column(Text)
    run_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
