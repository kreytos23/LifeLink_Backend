from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    phone = Column(String(30), nullable=True)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="provider")
    donor = relationship("Donor", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    organization_name = Column(String(150), nullable=True)
    organization_type = Column(String(80), nullable=True)
    description = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="profile")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class BloodType(Base):
    __tablename__ = "blood_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(5), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    blood_type_id = Column(Integer, ForeignKey("blood_types.id"), nullable=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=False, default=0)
    unit = Column(String(50), nullable=False)
    expiration_date = Column(Date, nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    urgency_level = Column(String(10), default="BAJA", nullable=False)
    status = Column(String(20), default="DISPONIBLE", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    provider = relationship("User", back_populates="inventory_items")
    category = relationship("Category")
    blood_type = relationship("BloodType")
    requests = relationship("Request", back_populates="inventory_item")

class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    blood_type_id = Column(Integer, ForeignKey("blood_types.id"), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    last_donation_date = Column(Date, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="donor")
    blood_type = relationship("BloodType")

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=True)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity_requested = Column(Integer, nullable=True)
    message = Column(Text, nullable=True)
    request_type = Column(String(20), nullable=False)
    status = Column(String(20), default="PENDIENTE", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    inventory_item = relationship("InventoryItem", back_populates="requests")
    donor = relationship("Donor")
    requester = relationship("User")
    status_history = relationship("RequestStatusHistory", back_populates="request", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("inventory_id IS NOT NULL OR donor_id IS NOT NULL", name="ck_request_target_required"),
    )

class RequestStatusHistory(Base):
    __tablename__ = "request_status_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request = relationship("Request", back_populates="status_history")
    changed_by_user = relationship("User")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=True)
    type = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
    request = relationship("Request")
