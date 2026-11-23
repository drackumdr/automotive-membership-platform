# Convenciones de la API

- Prefijo `/api/v1` (excepto `/health`).
- JSON, validación con Pydantic, OpenAPI automático en `/docs`.
- Identificadores UUID; montos en NUMERIC(14,2) (nunca float); fechas en UTC.
- Permisos verificados siempre en el backend.
