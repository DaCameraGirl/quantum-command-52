"""Add source URLs to housing and inventory records.

Revision ID: 003_add_source_urls_to_housing_inventory
Revises: 002_add_grant_source_url
Create Date: 2026-06-07
"""

from alembic import op


revision = "003_add_source_urls_to_housing_inventory"
down_revision = "002_add_grant_source_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE housing_incidents ADD COLUMN IF NOT EXISTS source_url TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE asset_inventory ADD COLUMN IF NOT EXISTS source_url TEXT NOT NULL DEFAULT ''")


def downgrade() -> None:
    op.execute("ALTER TABLE asset_inventory DROP COLUMN IF EXISTS source_url")
    op.execute("ALTER TABLE housing_incidents DROP COLUMN IF EXISTS source_url")
