"""initial enterprise schema

Revision ID: 001_initial_enterprise_schema
Revises:
Create Date: 2026-06-06
"""

from __future__ import annotations

from alembic import op

revision = "001_initial_enterprise_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id BIGSERIAL PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
            token TEXT PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS portfolio_assets (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            ticker TEXT NOT NULL,
            name TEXT NOT NULL,
            target_weight DOUBLE PRECISION NOT NULL CHECK (target_weight >= 0),
            paper_cash DOUBLE PRECISION NOT NULL CHECK (paper_cash >= 0),
            expected_return DOUBLE PRECISION NOT NULL,
            volatility DOUBLE PRECISION NOT NULL CHECK (volatility >= 0),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(user_id, ticker)
        );

        CREATE TABLE IF NOT EXISTS portfolio_history (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            source TEXT NOT NULL,
            total_cash DOUBLE PRECISION NOT NULL,
            weighted_return DOUBLE PRECISION NOT NULL,
            weighted_risk DOUBLE PRECISION NOT NULL,
            asset_count INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS quantum_telemetry_metrics (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            run_id TEXT NOT NULL,
            backend TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value DOUBLE PRECISION NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS grant_ledger (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            grant_name TEXT NOT NULL,
            funding_amount DOUBLE PRECISION NOT NULL CHECK (funding_amount >= 0),
            deadline DATE,
            application_difficulty INTEGER NOT NULL CHECK (application_difficulty BETWEEN 1 AND 5),
            priority_score DOUBLE PRECISION NOT NULL,
            status TEXT NOT NULL DEFAULT 'research',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS housing_incidents (
            incident_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            area_location TEXT NOT NULL,
            request_date DATE NOT NULL,
            resolve_date DATE,
            severity_level INTEGER NOT NULL CHECK (severity_level BETWEEN 1 AND 10),
            status TEXT NOT NULL DEFAULT 'open',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS asset_inventory (
            item_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            estimated_market_value DOUBLE PRECISION NOT NULL CHECK (estimated_market_value >= 0),
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            notes TEXT NOT NULL DEFAULT '',
            acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS real_estate_listings (
            listing_id BIGSERIAL PRIMARY KEY,
            tenant_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            agent_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            address_street TEXT NOT NULL,
            address_city TEXT NOT NULL,
            address_state TEXT NOT NULL,
            address_zip TEXT NOT NULL,
            price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
            status TEXT NOT NULL DEFAULT 'active',
            bedrooms INTEGER,
            bathrooms NUMERIC(3, 1),
            square_feet INTEGER,
            mls_number TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS real_estate_transactions (
            transaction_id BIGSERIAL PRIMARY KEY,
            tenant_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            listing_id BIGINT NOT NULL REFERENCES real_estate_listings(listing_id) ON DELETE RESTRICT,
            agent_id BIGINT NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
            buyer_name TEXT NOT NULL,
            contract_price NUMERIC(12, 2) NOT NULL CHECK (contract_price >= 0),
            escrow_company TEXT NOT NULL,
            earnest_money_amount NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (earnest_money_amount >= 0),
            target_closing_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'under_contract',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS transaction_milestones (
            milestone_id BIGSERIAL PRIMARY KEY,
            transaction_id BIGINT NOT NULL REFERENCES real_estate_transactions(transaction_id) ON DELETE CASCADE,
            milestone_name TEXT NOT NULL,
            due_date DATE NOT NULL,
            completed_at TIMESTAMPTZ,
            is_critical_drop_dead BOOLEAN NOT NULL DEFAULT TRUE,
            notes TEXT NOT NULL DEFAULT '',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS billing_accounts (
            billing_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES user_profiles(id) ON DELETE SET NULL,
            stripe_customer_id TEXT NOT NULL UNIQUE,
            subscription_tier TEXT NOT NULL DEFAULT 'free',
            account_status TEXT NOT NULL DEFAULT 'inactive',
            current_period_end TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS stripe_webhook_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            payload_json JSONB NOT NULL,
            received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            processed_at TIMESTAMPTZ
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_user_expires
            ON user_sessions(user_id, expires_at);
        CREATE INDEX IF NOT EXISTS idx_assets_user_weight
            ON portfolio_assets(user_id, target_weight DESC);
        CREATE INDEX IF NOT EXISTS idx_history_user_created
            ON portfolio_history(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_telemetry_user_run
            ON quantum_telemetry_metrics(user_id, run_id);
        CREATE INDEX IF NOT EXISTS idx_grants_user_priority
            ON grant_ledger(user_id, priority_score DESC, deadline ASC NULLS LAST);
        CREATE INDEX IF NOT EXISTS idx_grants_user_status
            ON grant_ledger(user_id, status);
        CREATE INDEX IF NOT EXISTS idx_housing_user_status_request
            ON housing_incidents(user_id, status, request_date DESC);
        CREATE INDEX IF NOT EXISTS idx_housing_user_severity
            ON housing_incidents(user_id, severity_level DESC, request_date DESC);
        CREATE INDEX IF NOT EXISTS idx_inventory_user_value
            ON asset_inventory(user_id, estimated_market_value DESC, quantity DESC);
        CREATE INDEX IF NOT EXISTS idx_inventory_user_category
            ON asset_inventory(user_id, category);
        CREATE INDEX IF NOT EXISTS idx_listings_tenant_status
            ON real_estate_listings(tenant_id, status, price DESC);
        CREATE INDEX IF NOT EXISTS idx_transactions_tenant_status
            ON real_estate_transactions(tenant_id, status, target_closing_date);
        CREATE INDEX IF NOT EXISTS idx_milestones_transaction_due
            ON transaction_milestones(transaction_id, due_date);
        CREATE INDEX IF NOT EXISTS idx_milestones_due
            ON transaction_milestones(due_date);
        CREATE INDEX IF NOT EXISTS idx_billing_accounts_user
            ON billing_accounts(user_id, account_status);
        CREATE INDEX IF NOT EXISTS idx_stripe_events_type_received
            ON stripe_webhook_events(event_type, received_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS stripe_webhook_events;
        DROP TABLE IF EXISTS billing_accounts;
        DROP TABLE IF EXISTS transaction_milestones;
        DROP TABLE IF EXISTS real_estate_transactions;
        DROP TABLE IF EXISTS real_estate_listings;
        DROP TABLE IF EXISTS asset_inventory;
        DROP TABLE IF EXISTS housing_incidents;
        DROP TABLE IF EXISTS grant_ledger;
        DROP TABLE IF EXISTS quantum_telemetry_metrics;
        DROP TABLE IF EXISTS portfolio_history;
        DROP TABLE IF EXISTS portfolio_assets;
        DROP TABLE IF EXISTS user_sessions;
        DROP TABLE IF EXISTS user_profiles;
        """
    )
