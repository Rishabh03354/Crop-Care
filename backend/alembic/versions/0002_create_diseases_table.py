"""Create the disease catalogue table.

Revision ID: 0002_create_diseases
Revises: 0001_create_predictions
Create Date: 2026-10-21
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_create_diseases"
down_revision: str | None = "0001_create_predictions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the disease catalogue table without altering predictions."""
    op.create_table(
        "diseases",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("display_name", sa.String(length=200), server_default=sa.text("''"), nullable=False),
        sa.Column("crop", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "symptoms",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column("causes", sa.Text(), server_default=sa.text("''"), nullable=True),
        sa.Column(
            "treatment",
            sa.JSON(),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column("severity", sa.String(length=20), server_default=sa.text("'medium'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_diseases_name"),
    )
    op.create_index("ix_diseases_name", "diseases", ["name"], unique=False)


def downgrade() -> None:
    """Remove only the disease catalogue table."""
    op.drop_index("ix_diseases_name", table_name="diseases")
    op.drop_table("diseases")
