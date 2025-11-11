from __future__ import annotations
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float,
    ForeignKey, Enum, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from backend.schemas.camera import CameraStatus
from backend.schemas.plate import PlateStatus


class Base(DeclarativeBase):
    pass


# models
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_plates = relationship("LicensePlate", back_populates="creator")
    detections = relationship("LicensePlateDetection", back_populates="operator")
    audit_logs = relationship("AuditLog", back_populates="user")


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    stream_url: Mapped[str | None] = mapped_column(String(500))
    stream_type: Mapped[str] = mapped_column(String(20), default="rtsp")
    fps: Mapped[int] = mapped_column(Integer, default=25)
    resolution_width: Mapped[int] = mapped_column(Integer, default=1920)
    resolution_height: Mapped[int] = mapped_column(Integer, default=1080)
    status: Mapped[CameraStatus] = mapped_column(Enum(CameraStatus), default=CameraStatus.INACTIVE)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    roi_x: Mapped[int] = mapped_column(Integer, default=0)
    roi_y: Mapped[int] = mapped_column(Integer, default=0)
    roi_width: Mapped[int] = mapped_column(Integer, default=1920)
    roi_height: Mapped[int] = mapped_column(Integer, default=1080)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    detections = relationship("LicensePlateDetection", back_populates="camera")


class LicensePlate(Base):
    __tablename__ = "license_plates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plate_text: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    plate_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    country_code: Mapped[str] = mapped_column(String(3), default="DZ")
    plate_type: Mapped[str | None] = mapped_column(String(20))
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_name: Mapped[str | None] = mapped_column(String(100))
    owner_contact: Mapped[str | None] = mapped_column(String(100))
    vehicle_info: Mapped[str | None] = mapped_column(Text)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    creator = relationship("User", back_populates="created_plates")
    detections = relationship("LicensePlateDetection", back_populates="plate")

    __table_args__ = (
        UniqueConstraint("plate_text", "country_code", name="uq_license_plate_text_country"),
    )


class LicensePlateDetection(Base):
    __tablename__ = "license_plate_detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    detected_plate_text: Mapped[str] = mapped_column(String(20), nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[PlateStatus] = mapped_column(Enum(PlateStatus), default=PlateStatus.UNKNOWN)
    thumbnail_path: Mapped[str | None] = mapped_column(String(255))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"))
    plate_id: Mapped[int | None] = mapped_column(ForeignKey("license_plates.id"))
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    camera = relationship("Camera", back_populates="detections")
    plate = relationship("LicensePlate", back_populates="detections")
    operator = relationship("User", back_populates="detections")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[int | None] = mapped_column(Integer)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    endpoint: Mapped[str | None] = mapped_column(String(200))
    details: Mapped[str | None] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
