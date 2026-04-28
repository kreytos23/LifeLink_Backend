from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .database import get_db
from . import models, schemas
from .security import hash_password, verify_password
from .business import (
    validate_role,
    validate_provider,
    validate_receiver,
    normalize_upper,
    VALID_URGENCY,
    VALID_INVENTORY_STATUS,
    VALID_REQUEST_STATUS,
    create_notification,
    create_history,
    can_donor_donate_to_receiver,
)

router = APIRouter(prefix="/api/v1")

@router.get("/health")
def health():
    return {"status": "UP", "service": "lifelink-backend"}

@router.post("/auth/register", response_model=schemas.UserResponse, status_code=201)
def register_user(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    role = validate_role(payload.role)

    existing = db.query(models.User).filter(
        or_(models.User.username == payload.username, models.User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="El username o email ya existe.")

    if role == "DONOR" and not payload.blood_type_id:
        raise HTTPException(status_code=400, detail="Para registrar un DONOR se requiere blood_type_id.")

    user = models.User(
        username=payload.username.strip(),
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        role=role,
    )
    db.add(user)
    db.flush()

    if payload.profile:
        profile = models.Profile(user_id=user.id, **payload.profile.model_dump())
        db.add(profile)

    if role == "DONOR":
        blood_type = db.get(models.BloodType, payload.blood_type_id)
        if not blood_type:
            raise HTTPException(status_code=404, detail="Tipo de sangre no encontrado.")
        donor = models.Donor(
            user_id=user.id,
            blood_type_id=payload.blood_type_id,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            is_available=True,
        )
        db.add(donor)

    db.commit()
    db.refresh(user)
    return user

@router.post("/auth/login", response_model=schemas.LoginResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo.")
    return {"message": "Login correcto", "user": user}

@router.get("/catalog/categories", response_model=list[schemas.CategoryResponse])
def list_categories(type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Category)
    if type:
        query = query.filter(models.Category.type == normalize_upper(type))
    return query.order_by(models.Category.name).all()

@router.get("/catalog/blood-types", response_model=list[schemas.BloodTypeResponse])
def list_blood_types(db: Session = Depends(get_db)):
    return db.query(models.BloodType).order_by(models.BloodType.name).all()

@router.post("/inventory", response_model=schemas.InventoryResponse, status_code=201)
def create_inventory_item(payload: schemas.InventoryCreate, db: Session = Depends(get_db)):
    provider = db.get(models.User, payload.provider_id)
    validate_provider(provider)

    category = db.get(models.Category, payload.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada.")

    urgency = normalize_upper(payload.urgency_level)
    if urgency not in VALID_URGENCY:
        raise HTTPException(status_code=400, detail="Urgencia inválida. Use BAJA, MEDIA o ALTA.")

    if payload.blood_type_id:
        if not db.get(models.BloodType, payload.blood_type_id):
            raise HTTPException(status_code=404, detail="Tipo de sangre no encontrado.")

    item = models.InventoryItem(
        provider_id=payload.provider_id,
        category_id=payload.category_id,
        blood_type_id=payload.blood_type_id,
        name=payload.name,
        description=payload.description,
        quantity=payload.quantity,
        unit=payload.unit,
        expiration_date=payload.expiration_date,
        latitude=payload.latitude,
        longitude=payload.longitude,
        urgency_level=urgency,
        status="DISPONIBLE",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("/inventory", response_model=list[schemas.InventoryResponse])
def search_inventory(
    category_id: Optional[int] = None,
    blood_type_id: Optional[int] = None,
    name: Optional[str] = None,
    urgency_level: Optional[str] = None,
    only_available: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(models.InventoryItem)
    if only_available:
        query = query.filter(models.InventoryItem.status == "DISPONIBLE", models.InventoryItem.quantity > 0)
    if category_id:
        query = query.filter(models.InventoryItem.category_id == category_id)
    if blood_type_id:
        query = query.filter(models.InventoryItem.blood_type_id == blood_type_id)
    if name:
        query = query.filter(models.InventoryItem.name.ilike(f"%{name}%"))
    if urgency_level:
        query = query.filter(models.InventoryItem.urgency_level == normalize_upper(urgency_level))
    return query.order_by(models.InventoryItem.created_at.desc()).all()

@router.get("/inventory/{inventory_id}", response_model=schemas.InventoryResponse)
def get_inventory_item(inventory_id: int, db: Session = Depends(get_db)):
    item = db.get(models.InventoryItem, inventory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Insumo no encontrado.")
    return item

@router.put("/inventory/{inventory_id}", response_model=schemas.InventoryResponse)
def update_inventory_item(inventory_id: int, payload: schemas.InventoryUpdate, provider_id: int = Query(...), db: Session = Depends(get_db)):
    item = db.get(models.InventoryItem, inventory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Insumo no encontrado.")
    if item.provider_id != provider_id:
        raise HTTPException(status_code=403, detail="No puedes modificar una publicación que no te pertenece.")

    data = payload.model_dump(exclude_unset=True)
    if "urgency_level" in data and data["urgency_level"]:
        data["urgency_level"] = normalize_upper(data["urgency_level"])
        if data["urgency_level"] not in VALID_URGENCY:
            raise HTTPException(status_code=400, detail="Urgencia inválida.")
    if "status" in data and data["status"]:
        data["status"] = normalize_upper(data["status"])
        if data["status"] not in VALID_INVENTORY_STATUS:
            raise HTTPException(status_code=400, detail="Estatus de inventario inválido.")
    for field, value in data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item

@router.get("/donors", response_model=list[schemas.DonorResponse])
def search_donors(blood_type_id: Optional[int] = None, only_available: bool = True, db: Session = Depends(get_db)):
    query = db.query(models.Donor)
    if only_available:
        query = query.filter(models.Donor.is_available == True)
    if blood_type_id:
        query = query.filter(models.Donor.blood_type_id == blood_type_id)
    return query.order_by(models.Donor.created_at.desc()).all()

@router.post("/requests/supplies", response_model=schemas.RequestResponse, status_code=201)
def request_supply(payload: schemas.SupplyRequestCreate, db: Session = Depends(get_db)):
    requester = db.get(models.User, payload.requester_id)
    validate_receiver(requester)

    item = db.get(models.InventoryItem, payload.inventory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Insumo no encontrado.")
    if item.status != "DISPONIBLE" or item.quantity <= 0:
        raise HTTPException(status_code=409, detail="El insumo no está disponible.")
    if payload.quantity_requested > item.quantity:
        raise HTTPException(status_code=409, detail="La cantidad solicitada supera la cantidad disponible.")
    if item.provider_id == payload.requester_id:
        raise HTTPException(status_code=400, detail="No puedes solicitar tu propia publicación.")

    request = models.Request(
        inventory_id=item.id,
        requester_id=requester.id,
        quantity_requested=payload.quantity_requested,
        message=payload.message,
        request_type="INSUMO",
        status="PENDIENTE",
    )
    db.add(request)
    db.flush()
    create_history(db, request.id, "PENDIENTE", requester.id, "Solicitud creada")
    create_notification(
        db,
        user_id=item.provider_id,
        request_id=request.id,
        type_="REQUEST_CREATED",
        title="Nueva solicitud de insumo",
        message=f"{requester.full_name} solicitó {payload.quantity_requested} {item.unit} de {item.name}.",
    )
    db.commit()
    db.refresh(request)
    return request

@router.post("/requests/blood", response_model=schemas.RequestResponse, status_code=201)
def request_blood_donation(payload: schemas.BloodDonationRequestCreate, db: Session = Depends(get_db)):
    requester = db.get(models.User, payload.requester_id)
    validate_receiver(requester)

    donor = db.get(models.Donor, payload.donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donador no encontrado.")
    if not donor.is_available:
        raise HTTPException(status_code=409, detail="El donador no está disponible.")
    if donor.user_id == requester.id:
        raise HTTPException(status_code=400, detail="No puedes solicitarte a ti mismo como donador.")

    request = models.Request(
        donor_id=donor.id,
        requester_id=requester.id,
        quantity_requested=None,
        message=payload.message,
        request_type="SANGRE",
        status="PENDIENTE",
    )
    db.add(request)
    db.flush()
    create_history(db, request.id, "PENDIENTE", requester.id, "Solicitud de donación creada")
    create_notification(
        db,
        user_id=donor.user_id,
        request_id=request.id,
        type_="BLOOD_REQUEST_CREATED",
        title="Nueva solicitud de donación",
        message=f"{requester.full_name} solicitó una donación de sangre.",
    )
    db.commit()
    db.refresh(request)
    return request

@router.get("/requests", response_model=list[schemas.RequestResponse])
def list_requests(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Request)
    if user_id:
        query = query.outerjoin(models.InventoryItem, models.Request.inventory_id == models.InventoryItem.id).outerjoin(models.Donor, models.Request.donor_id == models.Donor.id).filter(
            or_(
                models.Request.requester_id == user_id,
                models.InventoryItem.provider_id == user_id,
                models.Donor.user_id == user_id,
            )
        )
    if status:
        query = query.filter(models.Request.status == normalize_upper(status))
    if request_type:
        query = query.filter(models.Request.request_type == normalize_upper(request_type))
    return query.order_by(models.Request.created_at.desc()).all()

@router.get("/requests/{request_id}", response_model=schemas.RequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    request = db.get(models.Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    return request

@router.patch("/requests/{request_id}/status", response_model=schemas.RequestResponse)
def update_request_status(request_id: int, payload: schemas.RequestStatusUpdate, db: Session = Depends(get_db)):
    new_status = normalize_upper(payload.status)
    if new_status not in VALID_REQUEST_STATUS - {"PENDIENTE"}:
        raise HTTPException(status_code=400, detail="Estatus inválido. Use ACEPTADA, RECHAZADA, CANCELADA o COMPLETADA.")

    request = db.get(models.Request, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    if request.status in {"RECHAZADA", "CANCELADA", "COMPLETADA"}:
        raise HTTPException(status_code=409, detail="La solicitud ya está cerrada y no puede cambiarse.")

    actor = db.get(models.User, payload.user_id)
    if not actor:
        raise HTTPException(status_code=404, detail="Usuario actor no encontrado.")

    owner_user_id = None
    item = None
    donor = None

    if request.request_type == "INSUMO":
        item = db.get(models.InventoryItem, request.inventory_id)
        owner_user_id = item.provider_id
    elif request.request_type == "SANGRE":
        donor = db.get(models.Donor, request.donor_id)
        owner_user_id = donor.user_id


    if new_status in {"ACEPTADA", "RECHAZADA"} and actor.id != owner_user_id:
        raise HTTPException(status_code=403, detail="Solo el proveedor o donador puede aceptar/rechazar la solicitud.")
    if new_status == "CANCELADA" and actor.id != request.requester_id:
        raise HTTPException(status_code=403, detail="Solo el solicitante puede cancelar la solicitud.")
    if new_status == "COMPLETADA" and actor.id not in {owner_user_id, request.requester_id}:
        raise HTTPException(status_code=403, detail="Solo participantes de la solicitud pueden completarla.")

    if request.request_type == "INSUMO" and item:
        if new_status == "ACEPTADA":
            if request.status != "PENDIENTE":
                raise HTTPException(status_code=409, detail="Solo solicitudes pendientes pueden aceptarse.")
            if item.quantity < (request.quantity_requested or 0):
                raise HTTPException(status_code=409, detail="Inventario insuficiente para aceptar la solicitud.")
            item.quantity -= request.quantity_requested or 0
            if item.quantity == 0:
                item.status = "RESERVADO"
        elif new_status == "COMPLETADA":
            if request.status != "ACEPTADA":
                raise HTTPException(status_code=409, detail="Solo solicitudes aceptadas pueden completarse.")
            if item.quantity == 0:
                item.status = "ENTREGADO"

    if request.request_type == "SANGRE" and donor:
        if new_status == "ACEPTADA":
            if request.status != "PENDIENTE":
                raise HTTPException(status_code=409, detail="Solo solicitudes pendientes pueden aceptarse.")
            donor.is_available = False
        elif new_status in {"RECHAZADA", "CANCELADA"}:
            donor.is_available = True
        elif new_status == "COMPLETADA":
            if request.status != "ACEPTADA":
                raise HTTPException(status_code=409, detail="Solo solicitudes aceptadas pueden completarse.")
            donor.is_available = False

    request.status = new_status
    create_history(db, request.id, new_status, actor.id, payload.notes)

    create_notification(
        db,
        user_id=request.requester_id,
        request_id=request.id,
        type_="REQUEST_STATUS_CHANGED",
        title="Cambio de estatus de solicitud",
        message=f"Tu solicitud cambió a {new_status}.",
    )
    if owner_user_id != request.requester_id:
        create_notification(
            db,
            user_id=owner_user_id,
            request_id=request.id,
            type_="REQUEST_STATUS_CHANGED",
            title="Cambio de estatus de solicitud",
            message=f"La solicitud #{request.id} cambió a {new_status}.",
        )

    db.commit()
    db.refresh(request)
    return request

@router.get("/notifications", response_model=list[schemas.NotificationResponse])
def list_notifications(user_id: int, only_unread: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    if only_unread:
        query = query.filter(models.Notification.is_read == False)
    return query.order_by(models.Notification.created_at.desc()).all()

@router.patch("/notifications/{notification_id}/read", response_model=schemas.NotificationResponse)
def mark_notification_as_read(notification_id: int, user_id: int, db: Session = Depends(get_db)):
    notification = db.get(models.Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    if notification.user_id != user_id:
        raise HTTPException(status_code=403, detail="No puedes modificar una notificación de otro usuario.")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
