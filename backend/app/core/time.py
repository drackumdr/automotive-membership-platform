from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_utc(dt: datetime) -> datetime:
    """SQLite devuelve fechas sin zona; las tratamos como UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
