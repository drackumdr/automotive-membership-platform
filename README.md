# Automotive Membership Platform

Monorepo (nombre provisional) de la plataforma de membresías automotrices.
Backend FastAPI + PostgreSQL, frontend Flutter Web. Estado: **TASK-002 (identidad, usuarios, roles y permisos)**.

## Requisitos
- Python 3.12+, PostgreSQL 14+ (Windows o Ubuntu)
- Flutter 3.22+ (con soporte web)

## Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate      Ubuntu: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env  -> editar DATABASE_URL y JWT_SECRET
python -c "import secrets; print(secrets.token_urlsafe(48))"   # úsalo como JWT_SECRET
```
Crear la base en PostgreSQL (ejemplo): `CREATE DATABASE membership_dev;`

```bash
alembic upgrade head                      # migraciones
python -m app.cli seed                    # permisos y roles base (idempotente)
python -m app.cli create-superadmin --username admin --name "Tu nombre"   # pide la contraseña
uvicorn app.main:app --reload --port 8000 # API
pytest -q                                 # pruebas (no requieren PostgreSQL)
```
Comprobar: http://localhost:8000/health → `{"status":"ok","database":"ok",...}`
y documentación en http://localhost:8000/docs.

## Frontend
```bash
cd frontend
flutter create . --platforms=web   # genera web/ (no sobrescribe lib/ ni pubspec.yaml; revisa git status)
flutter pub get
flutter test
flutter run -d chrome --web-port 8080 --dart-define=API_BASE_URL=http://localhost:8000
```

## Reglas
- Sin credenciales en el repo: usar `.env` (ignorado por git). Hay una prueba que lo vigila.
- Dinero: NUMERIC(14,2). Reglas de negocio en `service.py`, no en routers.
- Siguiente entrega: **TASK-003 — Clientes y vehículos** (Sprint 2).

## Estructura
Ver `docs/` y la especificación técnica v1.1. Cada módulo de `backend/app/modules/` tendrá:
`models.py, schemas.py, repository.py, service.py, router.py, permissions.py, tests/`.
