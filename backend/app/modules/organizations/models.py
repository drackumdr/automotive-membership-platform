import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.database import Base

ORG_TYPES = ("CORPORATE", "OWNED_WORKSHOP", "AFFILIATE_WORKSHOP", "FRANCHISE")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
