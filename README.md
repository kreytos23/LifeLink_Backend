# LifeLink

Backend FastAPI + PostgreSQL para LifeLink.

## 1. Crear entorno virtual

```bash
cd backend
python -m venv venv
```

Windows PowerShell:

```bash
.\venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

## 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 3. Ejecutar API

Desde la carpeta `backend`:

```bash
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## 4. Usuarios de prueba

Los datos seed incluyen usuarios, pero para pruebas de login se recomienda registrar usuarios desde `/auth/register` porque así se genera el hash correcto en tu ambiente.


## 5. Flujo de negocio sugerido

### Registrar proveedor

POST `/api/v1/auth/register`

```json
{
  "username": "hospital_sur",
  "email": "hospital.sur@lifelink.test",
  "password": "lifelink123",
  "full_name": "Hospital Sur",
  "phone": "5551112222",
  "role": "PROVIDER",
  "profile": {
    "organization_name": "Hospital Sur",
    "organization_type": "Hospital",
    "address": "CDMX",
    "latitude": 19.4326,
    "longitude": -99.1332
  }
}
```

### Registrar receptor

POST `/api/v1/auth/register`

```json
{
  "username": "clinica_centro",
  "email": "clinica.centro@lifelink.test",
  "password": "lifelink123",
  "full_name": "Clínica Centro",
  "phone": "5553334444",
  "role": "RECEIVER",
  "profile": {
    "organization_name": "Clínica Centro",
    "organization_type": "Clínica",
    "address": "Centro, CDMX"
  }
}
```

### Registrar donador

POST `/api/v1/auth/register`

```json
{
  "username": "maria_donor",
  "email": "maria.donor@lifelink.test",
  "password": "lifelink123",
  "full_name": "María López",
  "phone": "5555556666",
  "role": "DONOR",
  "blood_type_id": 4,
  "date_of_birth": "1998-02-15",
  "gender": "FEMENINO"
}
```

### Login básico

POST `/api/v1/auth/login`

```json
{
  "username": "hospital_sur",
  "password": "lifelink123"
}
```

No se usa JWT. El backend devuelve el usuario y el frontend puede guardar temporalmente el `user.id` para enviarlo en las operaciones.

### Publicar insumo

POST `/api/v1/inventory`

```json
{
  "provider_id": 1,
  "category_id": 1,
  "name": "Solución salina 0.9%",
  "description": "Bolsas de 1000 ml",
  "quantity": 50,
  "unit": "bolsas",
  "expiration_date": "2027-01-31",
  "latitude": 19.4326,
  "longitude": -99.1332,
  "urgency_level": "MEDIA"
}
```

### Buscar insumos disponibles

GET `/api/v1/inventory?only_available=true`

Filtros soportados:

```text
category_id
blood_type_id
name
urgency_level
only_available
```

### Solicitar insumo

POST `/api/v1/requests/supplies`

```json
{
  "requester_id": 2,
  "inventory_id": 1,
  "quantity_requested": 10,
  "message": "Necesitamos solución salina para atención de emergencia."
}
```

### Aceptar solicitud de insumo

PATCH `/api/v1/requests/{request_id}/status`

```json
{
  "user_id": 1,
  "status": "ACEPTADA",
  "notes": "Solicitud aceptada. Coordinar entrega."
}
```

Cuando se acepta una solicitud de insumo, se descuenta la cantidad solicitada del inventario.

### Completar solicitud de insumo

PATCH `/api/v1/requests/{request_id}/status`

```json
{
  "user_id": 1,
  "status": "COMPLETADA",
  "notes": "Insumo entregado correctamente."
}
```

### Buscar donadores

GET `/api/v1/donors?only_available=true`

### Solicitar donación de sangre

POST `/api/v1/requests/blood`

```json
{
  "requester_id": 2,
  "donor_id": 1,
  "message": "Se solicita donación para paciente en urgencias."
}
```

### Aceptar solicitud de donación

PATCH `/api/v1/requests/{request_id}/status`

```json
{
  "user_id": 3,
  "status": "ACEPTADA",
  "notes": "Donador confirma disponibilidad."
}
```

Cuando una solicitud de sangre se acepta, el donador queda como no disponible.

## 7. Endpoints principales

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/register` | Registro de PROVIDER, RECEIVER o DONOR |
| POST | `/api/v1/auth/login` | Login básico sin JWT |
| GET | `/api/v1/catalog/categories` | Lista categorías |
| GET | `/api/v1/catalog/blood-types` | Lista tipos de sangre |
| POST | `/api/v1/inventory` | Publicar insumo |
| GET | `/api/v1/inventory` | Buscar insumos |
| GET | `/api/v1/inventory/{id}` | Ver insumo |
| PUT | `/api/v1/inventory/{id}?provider_id=1` | Actualizar publicación |
| GET | `/api/v1/donors` | Buscar donadores |
| POST | `/api/v1/requests/supplies` | Solicitar insumo |
| POST | `/api/v1/requests/blood` | Solicitar donación |
| GET | `/api/v1/requests` | Listar solicitudes |
| GET | `/api/v1/requests/{id}` | Ver solicitud |
| PATCH | `/api/v1/requests/{id}/status` | Cambiar estado de solicitud |
| GET | `/api/v1/notifications?user_id=1` | Ver notificaciones |
| PATCH | `/api/v1/notifications/{id}/read?user_id=1` | Marcar notificación como leída |

## 8. Reglas de negocio implementadas

- Solo `PROVIDER` puede publicar insumos.
- `RECEIVER` y `PROVIDER` pueden solicitar insumos o sangre.
- Un usuario no puede solicitar su propia publicación.
- Un donador no puede solicitarse a sí mismo.
- Para solicitudes de insumos:
  - Se valida disponibilidad.
  - Se valida cantidad suficiente.
  - Al aceptar, se descuenta la cantidad del inventario.
  - Si la cantidad llega a cero, el inventario pasa a `RESERVADO`.
  - Al completar, si ya no hay inventario, pasa a `ENTREGADO`.
- Para solicitudes de sangre:
  - Se valida que el donador exista y esté disponible.
  - Al aceptar, el donador queda no disponible.
- Se genera historial de estados.
- Se generan notificaciones básicas.

