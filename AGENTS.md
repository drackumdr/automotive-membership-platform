# AGENTS.md — automotive-membership-platform (taller)

Guía para agentes de código que trabajen en este repo. Fuente única de
instrucciones compartida entre agentes; `CLAUDE.md` solo la referencia.

## Qué es este repo

Monorepo de la plataforma de servicios y membresías automotrices (nombre provisional en mockup v3: **Autoserv**).

- **Primera etapa (alcance actual):** operación centralizada en un solo taller propio
  (`OWNED_WORKSHOP`). Cubre clientes, vehículos, planes y contratos, cobranza programada,
  solicitudes de servicio, recepción e inspección con evidencia, diagnóstico y presupuestos,
  autorizaciones, órdenes de trabajo con inventario básico, entrega, historial y reportes.
- **Evolución futura:** red de talleres afiliados / franquicias (`AFFILIATE_WORKSHOP`,
  `FRANCHISE`). El modelo de organizaciones ya deja preparada la jerarquía, sin
  sobre-construir flujos de afiliados antes de tiempo (YAGNI).

### Estructura actual

- `backend/` — FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL (`psycopg`), Argon2id + JWT/refresh rotativo, RBAC con alcance por organización, auditoría (`audit_logs`) y CLI (`python -m app.cli seed | create-superadmin`). Estado actual: **TASK-002** (`identity` y `organizations` implementados; 41 pruebas `pytest` pasando sin PostgreSQL). Siguiente entrega: **TASK-003 (Clientes y vehículos)**. Los demás módulos (`customers`, `vehicles`, `contracts`, `billing`, `repairs`, `authorizations`, `inventory`, `finance`, `catalog`, `notifications`, `reporting`, `workshops`) son stubs.
- `frontend/` — Flutter Web + PWA (`membership_app`), actualmente solo con `HealthPage` y prueba base (aún sin carpeta `web/` generada).
- `docs/` — documentación técnica (`security-model.md` y `api/conventions.md` completos; el resto son placeholders de la especificación v1.1).
- `deployment/` — ejemplos de Nginx, systemd, `.env` y script `dev-setup.sh`.

## Reglas de trabajo (ponytail activo)

Este repo tiene el plugin Ponytail activo en modo `full`. Respeta la
escalera antes de escribir código:

1. ¿Esto necesita existir? → si no, no lo escribas (YAGNI)
2. ¿Ya existe en este repo? → reutilízalo, no lo reescribas
3. ¿Lo hace el stdlib? → úsalo
4. ¿Lo hace la plataforma? → úsala
5. ¿Ya hay una dependencia instalada que lo haga? → úsala
6. ¿Una línea basta? → una línea
7. Solo entonces: el mínimo que funcione

La pereza nunca aplica a: validación de fronteras, manejo de datos,
seguridad o accesibilidad.

### Registro de deuda técnica (ponytail)

- Si realizas una simplificación deliberada que recorte una esquina técnica
  con un límite conocido (timeout fijo, heurística simple, O(n²)), márcalo
  obligatoriamente con un comentario:
  `# ponytail: <límite conocido y camino de migración>` (o `// ponytail:` en Dart/JS).
  Esto permite auditar la deuda con `/ponytail-debt`.

## Protocolo de Memoria (MemPalace)

El proyecto cuenta con el wing `taller` en MemPalace (vía MCP o CLI `mempalace`):
- **Al despertar o consultar decisiones previas:** usa `mempalace_search` (o `mempalace search "<consulta>" --wing taller`) antes de asumir o reinventar decisiones de producto o arquitectura.
- **Al cerrar una sesión con cambios o decisiones relevantes:** registra un resumen con `mempalace_diary_write` especificando `wing="taller"` y sincroniza archivos nuevos con `mempalace mine . --wing taller`.

## Convenciones

- Comentarios, nombres, mensajes de commit y strings de usuario: en español.
- Backend: prefijo `/api/v1` (excepto `/health`), UUIDs, montos en `NUMERIC(14,2)` (nunca `float`), fechas UTC, reglas de negocio en `service.py` (no en routers) y permisos siempre validados en backend.
- Sin dependencias nuevas sin necesidad real: revisa `backend/requirements.txt` y `frontend/pubspec.yaml` antes de agregar paquetes.
- Cada módulo nuevo en `backend/app/modules/` sigue el esquema: `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py`, `permissions.py`, `tests/`.

## Verificar antes de dar por terminado

Siempre que cambies código, corre la verificación del lado tocado:

- **Backend:**
  ```bash
  cd backend
  pytest -q
  ```
- **Frontend (Flutter):**
  ```bash
  cd frontend
  flutter analyze
  flutter test
  ```

Si algo falla, arréglalo tú antes de decir que terminaste.

## Advertencias de este entorno

- No subas `.env` ni credenciales (`backend/tests/security/test_no_secrets.py` falla si detecta secretos hardcodeados).
