"""Create the `predictions` table.

Revision ID: 0001_create_predictions
Revises:
Create Date: 2026-10-10

Notes
-----
This migration is intentionally minimal: it only creates the `predictions`
table and its two indexes. It does not touch any other table, does not drop
anything, and is safe to run against an existing database.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_predictions"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("image_path", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("crop_name", sa.String(length=100), nullable=True),
        sa.Column("disease_name", sa.String(length=200), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_predictions_confidence_range",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_status", "predictions", ["status"], unique=False)
    op.create_index(
        "ix_predictions_created_at", "predictions", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_predictions_created_at", table_name="predictions")
    op.drop_index("ix_predictions_status", table_name="predictions")
    op.drop_table("predictions")
