from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models

VALID_ROLES = {"PROVIDER", "RECEIVER", "DONOR"}
VALID_URGENCY = {"BAJA", "MEDIA", "ALTA"}
VALID_INVENTORY_STATUS = {"DISPONIBLE", "RESERVADO", "ENTREGADO", "EXPIRADO"}
VALID_REQUEST_STATUS = {"PENDIENTE", "ACEPTADA", "RECHAZADA", "CANCELADA", "COMPLETADA"}

BLOOD_COMPATIBILITY = {
    "O-": ["O-"],
    "O+": ["O-", "O+"],
    "A-": ["O-", "A-"],
    "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"],
    "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}

def normalize_upper(value: str) -> str:
    return value.strip().upper()

def validate_role(role: str) -> str:
    role = normalize_upper(role)
    if role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Rol inválido. Use PROVIDER, RECEIVER o DONOR.")
    return role

def validate_provider(user: models.User):
    if not user or user.role != "PROVIDER":
        raise HTTPException(status_code=403, detail="Solo un usuario PROVIDER puede publicar insumos.")

def validate_receiver(user: models.User):
    if not user or user.role not in {"RECEIVER", "PROVIDER"}:
        raise HTTPException(status_code=403, detail="Solo RECEIVER o PROVIDER pueden realizar solicitudes.")

def create_notification(db: Session, user_id: int, title: str, message: str, type_: str, request_id: int | None = None):
    notification = models.Notification(
        user_id=user_id,
        request_id=request_id,
        type=type_,
        title=title,
        message=message,
    )
    db.add(notification)
    return notification

def create_history(db: Session, request_id: int, status: str, changed_by: int | None, notes: str | None = None):
    history = models.RequestStatusHistory(
        request_id=request_id,
        status=status,
        changed_by=changed_by,
        notes=notes,
    )
    db.add(history)
    return history

def can_donor_donate_to_receiver(donor_blood_name: str, receiver_blood_name: str) -> bool:
    allowed_donors = BLOOD_COMPATIBILITY.get(receiver_blood_name.upper(), [])
    return donor_blood_name.upper() in allowed_donors
