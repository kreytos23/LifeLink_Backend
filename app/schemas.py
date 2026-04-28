from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

class ProfileCreate(BaseModel):
    organization_name: Optional[str] = None
    organization_type: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    phone: Optional[str] = None
    role: str = Field(description="PROVIDER | RECEIVER | DONOR")
    profile: Optional[ProfileCreate] = None
    blood_type_id: Optional[int] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    message: str
    user: UserResponse

class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str]

    class Config:
        from_attributes = True

class BloodTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True

class InventoryCreate(BaseModel):
    provider_id: int
    category_id: int
    blood_type_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    quantity: int = Field(gt=0)
    unit: str
    expiration_date: Optional[date] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    urgency_level: str = "BAJA"

class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=0)
    unit: Optional[str] = None
    expiration_date: Optional[date] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    urgency_level: Optional[str] = None
    status: Optional[str] = None

class InventoryResponse(BaseModel):
    id: int
    provider_id: int
    category_id: int
    blood_type_id: Optional[int]
    name: str
    description: Optional[str]
    quantity: int
    unit: str
    expiration_date: Optional[date]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    urgency_level: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class SupplyRequestCreate(BaseModel):
    requester_id: int
    inventory_id: int
    quantity_requested: int = Field(gt=0)
    message: Optional[str] = None

class BloodDonationRequestCreate(BaseModel):
    requester_id: int
    donor_id: int
    message: Optional[str] = None

class RequestStatusUpdate(BaseModel):
    user_id: int
    status: str = Field(description="ACEPTADA | RECHAZADA | CANCELADA | COMPLETADA")
    notes: Optional[str] = None

class RequestResponse(BaseModel):
    id: int
    inventory_id: Optional[int]
    donor_id: Optional[int]
    requester_id: int
    quantity_requested: Optional[int]
    message: Optional[str]
    request_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DonorResponse(BaseModel):
    id: int
    user_id: int
    blood_type_id: int
    date_of_birth: Optional[date]
    gender: Optional[str]
    last_donation_date: Optional[date]
    is_available: bool

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    request_id: Optional[int]
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
