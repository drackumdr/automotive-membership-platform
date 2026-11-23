"""baseline: punto de partida del esquema (sin tablas aún)

Revision ID: 0001
Revises:
Create Date: 2026-11-23
"""
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Las tablas de identidad llegan en TASK-002.
    pass


def downgrade() -> None:
    pass
