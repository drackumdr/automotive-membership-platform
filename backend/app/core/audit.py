"""Registro de auditoría (IAM-009). No hace commit: lo hace quien lo invoca."""
import uuid

from sqlalchemy.orm import Session

from app.modules.identity.models import AuditLog


def record(
    db: Session,
    action: str,
    *,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | str | None = None,
    organization_id: uuid.UUID | None = None,
    ip: str | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            organization_id=organization_id,
            ip=ip,
            details=details,
        )
    )
