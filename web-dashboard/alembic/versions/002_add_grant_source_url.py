"""add source url to grant ledger

Revision ID: 002_add_grant_source_url
Revises: 001_initial_enterprise_schema
Create Date: 2026-06-07
"""

from __future__ import annotations

from alembic import op

revision = "002_add_grant_source_url"
down_revision = "001_initial_enterprise_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE grant_ledger ADD COLUMN IF NOT EXISTS source_url TEXT NOT NULL DEFAULT ''")


def downgrade() -> None:
    op.execute("ALTER TABLE grant_ledger DROP COLUMN IF EXISTS source_url")
