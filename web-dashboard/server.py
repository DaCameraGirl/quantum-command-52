from __future__ import annotations

import csv
import hashlib
import hmac
import json
import math
import mimetypes
import os
import secrets
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

import jwt
from app_config import AppSettings, load_settings_from_env
from psycopg2 import errors
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.pool import ThreadedConnectionPool


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
ENV_FILE = REPO_ROOT / ".env"
SEED_CSV = REPO_ROOT / "output" / "paper_portfolio_plan.csv"
STATIC_ROOT = ROOT / "dist"
OPENAPI_SPEC = ROOT / "openapi.json"
DEFAULT_ASSETS = [
    ("BTC", "Bitcoin", 0.2424, 242.36, 0.24, 0.46),
    ("ETH", "Ethereum", 0.2389, 238.88, 0.18, 0.42),
    ("SOL", "Solana", 0.2394, 239.42, 0.35, 0.62),
    ("NVDA", "NVIDIA Corp", 0.2793, 279.34, 0.28, 0.38),
]

POOL: ThreadedConnectionPool | None = None
SETTINGS: AppSettings | None = None
RATE_LIMIT_LOCK = threading.Lock()
RATE_LIMIT_BUCKETS: dict[str, list[float]] = {}
SENSITIVE_LOG_KEYS = {"secret", "password", "token", "key", "database_url", "dsn"}
STRIPE_CHECKOUT_ENDPOINT = "https://api.stripe.com/v1/checkout/sessions"
REQUIRED_ALEMBIC_REVISION = "001_initial_enterprise_schema"
DEMO_SQLITE_FILE = ROOT / "data.db"
DEMO_LOCK = threading.RLock()
DEMO_USER = {
    "id": 1,
    "email": "angela@data-analytics.local",
    "display_name": "Angela Demo",
    "password_hash": "",
}
DEMO_DB: dict[str, list[dict]] = {
    "grants": [],
    "housing": [],
    "inventory": [],
    "transactions": [],
}
DEMO_TABLES = {
    "grants": ("demo_grants", "id"),
    "housing": ("demo_housing", "incident_id"),
    "inventory": ("demo_inventory", "item_id"),
    "transactions": ("demo_transactions", "transactionId"),
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def log_event(event: str, **fields) -> None:
    safe_fields = {
        key: "[redacted]" if any(marker in key.lower() for marker in SENSITIVE_LOG_KEYS) else value
        for key, value in fields.items()
    }
    payload = {
        "ts": utc_now().isoformat(),
        "event": event,
        **safe_fields,
    }
    print(json.dumps(payload, default=str), flush=True)


def load_dotenv_file() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_app_settings() -> AppSettings:
    global SETTINGS
    SETTINGS = load_settings_from_env()
    return SETTINGS


def settings() -> AppSettings:
    global SETTINGS
    if SETTINGS is None:
        SETTINGS = load_settings_from_env()
    return SETTINGS


def jwt_secret() -> str:
    return settings().jwt_secret.get_secret_value()


def allowed_origins() -> set[str]:
    return settings().allowed_origin_set


def cookie_secure() -> bool:
    return settings().cookie_secure


def access_token_max_age() -> int:
    return settings().jwt_ttl_seconds


def local_demo_mode() -> bool:
    return settings().local_demo_mode


def init_pool() -> None:
    global POOL
    if POOL is not None:
        return
    config = settings()
    POOL = ThreadedConnectionPool(
        minconn=config.database_pool_min,
        maxconn=config.database_pool_max,
        dsn=config.database_url.get_secret_value(),
    )


@contextmanager
def db_cursor(commit: bool = False) -> Iterator[RealDictCursor]:
    if POOL is None:
        raise RuntimeError("Database pool is not initialized.")
    connection = POOL.getconn()
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        POOL.putconn(connection)


def init_db() -> None:
    with db_cursor(commit=True) as cursor:
        cursor.execute(
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


def require_alembic_schema() -> None:
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT version_num
            FROM alembic_version
            WHERE version_num = %s
            """,
            (REQUIRED_ALEMBIC_REVISION,),
        )
        row = cursor.fetchone()
    if not row:
        raise RuntimeError(
            "Alembic migration check failed. Run `alembic upgrade head` before starting the production server."
        )


def next_demo_id(table: str, key: str) -> int:
    rows = DEMO_DB[table]
    return max([int(row[key]) for row in rows], default=0) + 1


def parse_demo_date(value):
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    return datetime.strptime(text[:10], "%Y-%m-%d").date()


def normalize_demo_row(table: str, row: dict) -> dict:
    if table == "grants":
        row["deadline"] = parse_demo_date(row.get("deadline"))
    elif table == "housing":
        row["request_date"] = parse_demo_date(row.get("request_date"))
        row["resolve_date"] = parse_demo_date(row.get("resolve_date"))
        row = enrich_housing_incident(row)
    elif table == "inventory":
        row = enrich_inventory_item(row)
    elif table == "transactions":
        row["closingDate"] = parse_demo_date(row.get("closingDate"))
        for milestone in row.get("milestones", []):
            milestone["dueDate"] = parse_demo_date(milestone.get("dueDate"))
            milestone["risk"] = transaction_milestone_risk(
                {
                    "due_date": milestone["dueDate"],
                    "completed_at": milestone.get("completedAt"),
                    "is_critical_drop_dead": milestone.get("critical", True),
                }
            )
    return row


def init_demo_sqlite() -> None:
    DEMO_SQLITE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DEMO_SQLITE_FILE) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        for table_name, key_name in DEMO_TABLES.values():
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {key_name} INTEGER PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        connection.commit()


def load_demo_memory_from_sqlite() -> None:
    with DEMO_LOCK:
        for table in DEMO_DB:
            DEMO_DB[table] = []
        with sqlite3.connect(DEMO_SQLITE_FILE) as connection:
            for logical_name, (table_name, key_name) in DEMO_TABLES.items():
                rows = connection.execute(
                    f"SELECT {key_name}, payload_json FROM {table_name} ORDER BY {key_name}"
                ).fetchall()
                DEMO_DB[logical_name] = [
                    normalize_demo_row(logical_name, json.loads(payload_json))
                    for _, payload_json in rows
                ]


def save_demo_memory_to_sqlite() -> None:
    init_demo_sqlite()
    with DEMO_LOCK:
        with sqlite3.connect(DEMO_SQLITE_FILE) as connection:
            for logical_name, (table_name, key_name) in DEMO_TABLES.items():
                connection.execute(f"DELETE FROM {table_name}")
                rows = [
                    (int(row[key_name]), json.dumps(row, default=str))
                    for row in DEMO_DB[logical_name]
                ]
                connection.executemany(
                    f"""
                    INSERT INTO {table_name} ({key_name}, payload_json, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    rows,
                )
            connection.commit()


def demo_assets() -> list[dict]:
    now = utc_now()
    return [
        {
            "ticker": ticker,
            "name": name,
            "target_weight": weight,
            "paper_cash": cash,
            "expected_return": expected_return,
            "volatility": volatility,
            "updated_at": now,
        }
        for ticker, name, weight, cash, expected_return, volatility in DEFAULT_ASSETS
    ]


def demo_portfolio_payload() -> dict:
    assets = demo_assets()
    summary = summarize_assets(assets)
    return {
        "summary": summary,
        "assets": assets,
        "history": [
            {
                "source": "demo_sqlite",
                "total_cash": summary["totalCash"],
                "weighted_return": summary["weightedReturn"],
                "weighted_risk": summary["weightedRisk"],
                "asset_count": summary["assetCount"],
                "created_at": utc_now(),
            }
        ],
        "telemetry": [
            {
                "run_id": "demo-local",
                "backend": "memory",
                "metric_name": "weighted_return",
                "metric_value": summary["weightedReturn"],
                "created_at": utc_now(),
            },
            {
                "run_id": "demo-local",
                "backend": "memory",
                "metric_name": "weighted_risk",
                "metric_value": summary["weightedRisk"],
                "created_at": utc_now(),
            },
        ],
    }


def seed_demo_memory() -> None:
    init_demo_sqlite()
    load_demo_memory_from_sqlite()
    if any(DEMO_DB[table] for table in DEMO_DB):
        log_event(
            "demo_sqlite_loaded",
            database=str(DEMO_SQLITE_FILE),
            grants=len(DEMO_DB["grants"]),
            housing=len(DEMO_DB["housing"]),
            inventory=len(DEMO_DB["inventory"]),
            transactions=len(DEMO_DB["transactions"]),
        )
        return

    grant_rows = [
        {
            "grant_name": "Women in Analytics Emergency Scholarship",
            "funding_amount": 7500.0,
            "deadline": shift_date(12),
            "application_difficulty": 2,
            "status": "ready",
        },
        {
            "grant_name": "Small Business Digital Tools Award",
            "funding_amount": 12000.0,
            "deadline": shift_date(28),
            "application_difficulty": 3,
            "status": "research",
        },
        {
            "grant_name": "Continuing Education Support Fund",
            "funding_amount": 4200.0,
            "deadline": shift_date(6),
            "application_difficulty": 1,
            "status": "ready",
        },
    ]
    for index, grant in enumerate(grant_rows, start=1):
        DEMO_DB["grants"].append(
            {
                "id": index,
                **grant,
                "priority_score": calculate_grant_priority(
                    funding_amount=grant["funding_amount"],
                    deadline=grant["deadline"],
                    application_difficulty=grant["application_difficulty"],
                    status=grant["status"],
                ),
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
        )

    DEMO_DB["housing"].extend(
        [
            enrich_housing_incident(
                {
                    "incident_id": 1,
                    "category": "Maintenance",
                    "description": "Water staining spreading under kitchen ceiling vent.",
                    "area_location": "Kitchen ceiling",
                    "request_date": shift_date(-9),
                    "resolve_date": None,
                    "severity_level": 7,
                    "status": "requested",
                    "created_at": utc_now(),
                    "updated_at": utc_now(),
                }
            ),
            enrich_housing_incident(
                {
                    "incident_id": 2,
                    "category": "Safety",
                    "description": "Exterior stair light does not turn on after dark.",
                    "area_location": "Front stairwell",
                    "request_date": shift_date(-3),
                    "resolve_date": None,
                    "severity_level": 8,
                    "status": "open",
                    "created_at": utc_now(),
                    "updated_at": utc_now(),
                }
            ),
        ]
    )

    DEMO_DB["inventory"].extend(
        [
            enrich_inventory_item(
                {
                    "item_id": 1,
                    "item_name": "Nikon Z6 II Camera Kit",
                    "category": "Camera Gear",
                    "estimated_market_value": 1450.0,
                    "quantity": 1,
                    "notes": "Body, lens, batteries, charger.",
                    "acquired_at": utc_now(),
                    "created_at": utc_now(),
                    "updated_at": utc_now(),
                }
            ),
            enrich_inventory_item(
                {
                    "item_id": 2,
                    "item_name": "Tang Sancai Ceramic Reference Piece",
                    "category": "Collectibles",
                    "estimated_market_value": 325.0,
                    "quantity": 2,
                    "notes": "Demo catalog example for historical-object tracking.",
                    "acquired_at": utc_now(),
                    "created_at": utc_now(),
                    "updated_at": utc_now(),
                }
            ),
        ]
    )

    DEMO_DB["transactions"].extend(
        [
            demo_transaction(
                transaction_id=1,
                stage="listing",
                address="418 Harbor View Lane",
                city="Charleston",
                state="SC",
                zip_code="29401",
                price=485000,
                client="Seller file",
                escrow="Pending offer",
                earnest_money=0,
                closing_offset=42,
                milestones=[
                    ("Seller disclosure packet", 2, False, True, "Upload signed disclosure before offer review."),
                    ("MLS photo review", 4, False, False, "Confirm image order and feature sheet."),
                    ("Offer review window", 9, False, True, "Calendar seller response deadline."),
                ],
            ),
            demo_transaction(
                transaction_id=2,
                stage="under_contract",
                address="92 Cedar Mill Court",
                city="Raleigh",
                state="NC",
                zip_code="27601",
                price=612500,
                client="Buyer file",
                escrow="Atlantic Title",
                earnest_money=18500,
                closing_offset=28,
                milestones=[
                    ("Inspection contingency", 1, False, True, "Deposit exposure begins if missed."),
                    ("Appraisal ordered", 5, False, True, "Confirm lender order and access."),
                    ("Loan approval deadline", 13, False, True, "Financing condition drop-dead date."),
                ],
            ),
            demo_transaction(
                transaction_id=3,
                stage="closing",
                address="1509 Ridgecrest Avenue",
                city="Nashville",
                state="TN",
                zip_code="37203",
                price=524900,
                client="Relocation file",
                escrow="Keystone Settlement",
                earnest_money=16000,
                closing_offset=5,
                milestones=[
                    ("Clear to close", 0, False, True, "Confirm final lender status."),
                    ("Wire instructions verified", 2, False, True, "Call title company before transfer."),
                    ("Closing appointment", 5, False, True, "Final signature window."),
                ],
            ),
        ]
    )
    save_demo_memory_to_sqlite()
    log_event(
        "demo_sqlite_seeded",
        database=str(DEMO_SQLITE_FILE),
        grants=len(DEMO_DB["grants"]),
        housing=len(DEMO_DB["housing"]),
        inventory=len(DEMO_DB["inventory"]),
        transactions=len(DEMO_DB["transactions"]),
    )


def demo_transaction(
    *,
    transaction_id: int,
    stage: str,
    address: str,
    city: str,
    state: str,
    zip_code: str,
    price: float,
    client: str,
    escrow: str,
    earnest_money: float,
    closing_offset: int,
    milestones: list[tuple[str, int, bool, bool, str]],
) -> dict:
    shaped_milestones = []
    for index, (name, offset, completed, critical, notes) in enumerate(milestones, start=1):
        due_date = shift_date(offset)
        milestone = {
            "id": transaction_id * 100 + index,
            "name": name,
            "dueDate": due_date,
            "completed": completed,
            "completedAt": utc_now() if completed else None,
            "critical": critical,
            "notes": notes,
        }
        milestone["risk"] = transaction_milestone_risk(
            {
                "due_date": due_date,
                "completed_at": milestone["completedAt"],
                "is_critical_drop_dead": critical,
            }
        )
        shaped_milestones.append(milestone)

    return {
        "id": f"TX-{transaction_id}",
        "transactionId": transaction_id,
        "listingId": transaction_id,
        "stage": stage,
        "address": address,
        "city": city,
        "state": state,
        "zip": zip_code,
        "price": float(price),
        "listingPrice": float(price),
        "agent": DEMO_USER["display_name"],
        "client": client,
        "escrow": escrow,
        "earnestMoney": float(earnest_money),
        "closingDate": shift_date(closing_offset),
        "milestones": shaped_milestones,
    }


def demo_grants_payload() -> dict:
    grants = sorted(
        DEMO_DB["grants"],
        key=lambda grant: (-float(grant["priority_score"]), grant["deadline"] or date.max, -float(grant["funding_amount"])),
    )
    active_grants = [grant for grant in grants if grant["status"] not in {"denied", "archived"}]
    return {
        "summary": {
            "grantCount": len(grants),
            "activeGrantCount": len(active_grants),
            "totalFunding": round(sum(float(grant["funding_amount"]) for grant in active_grants), 2),
            "topPriorityScore": float(grants[0]["priority_score"]) if grants else 0,
        },
        "grants": grants,
    }


def demo_housing_payload() -> dict:
    incidents = [enrich_housing_incident(incident) for incident in DEMO_DB["housing"]]
    open_incidents = [item for item in incidents if item["status"] not in {"resolved", "closed"}]
    overdue_incidents = [item for item in incidents if item["violation_flag"] not in {"resolved", "tracking"}]
    return {
        "summary": {
            "incidentCount": len(incidents),
            "openIncidentCount": len(open_incidents),
            "overdueCount": len(overdue_incidents),
            "maxDaysUnresolved": max([item["days_unresolved"] for item in open_incidents], default=0),
        },
        "incidents": incidents,
    }


def demo_inventory_payload() -> dict:
    items = [enrich_inventory_item(item) for item in DEMO_DB["inventory"]]
    total_value = sum(float(item["total_estimated_value"]) for item in items)
    categories = sorted({item["category"] for item in items})
    return {
        "summary": {
            "itemCount": len(items),
            "categoryCount": len(categories),
            "totalEstimatedValue": round(total_value, 2),
            "topItemValue": max([float(item["total_estimated_value"]) for item in items], default=0),
        },
        "items": items,
    }


def demo_transactions_payload() -> dict:
    deals = list(DEMO_DB["transactions"])
    active_deals = [deal for deal in deals if deal["stage"] != "closed"]
    all_milestones = [milestone for deal in deals for milestone in deal["milestones"]]
    due_this_week = [
        milestone
        for milestone in all_milestones
        if not milestone["completed"] and 0 <= (milestone["dueDate"] - date.today()).days <= 7
    ]
    breached = [milestone for milestone in all_milestones if milestone.get("risk") == "breach"]
    return {
        "summary": {
            "activeDealCount": len(active_deals),
            "activeDealValue": round(sum(float(deal["price"]) for deal in active_deals), 2),
            "earnestExposure": round(sum(float(deal["earnestMoney"]) for deal in active_deals), 2),
            "deadlineBreachCount": len(breached),
            "dueThisWeekCount": len(due_this_week),
        },
        "deals": deals,
    }


def normalized_weights(raw_scores: list[float]) -> list[float]:
    scores = [max(float(score), 0.001) for score in raw_scores]
    total = sum(scores) or 1.0
    return [score / total for score in scores]


def optimizer_payload(mode: str) -> dict:
    normalized_mode = str(mode or "classical").strip().lower()
    if normalized_mode not in {"classical", "quantum"}:
        normalized_mode = "classical"

    source_assets = [
        {
            "ticker": ticker,
            "name": name,
            "expected_return": expected_return,
            "volatility": volatility,
        }
        for ticker, name, _weight, _cash, expected_return, volatility in DEFAULT_ASSETS
    ]

    if normalized_mode == "classical":
        raw_scores = [
            asset["expected_return"] / (asset["volatility"] + 0.08)
            for asset in source_assets
        ]
        label = "Classical risk-adjusted solver"
        backend = "local scipy-style paper solver"
        description = "Deterministic Sharpe-style scoring for practical paper allocation analysis."
        artifact_command = "py -3.11 strict_macro_quantum_v10.py --optimizer-mode classical"
        convergence = [
            {"cycle": cycle, "score": round(0.42 + cycle * 0.047, 4), "loss": round(0.58 - cycle * 0.041, 4)}
            for cycle in range(1, 9)
        ]
    else:
        raw_scores = []
        for index, asset in enumerate(source_assets):
            phase = 1.15 + math.sin((index + 1) * 1.618) * 0.22
            qubo_value = max(asset["expected_return"] - asset["volatility"] * 0.18, 0.01)
            raw_scores.append(qubo_value * phase)
        label = "Quantum QAOA dashboard preview"
        backend = "fast local QAOA preview"
        description = "Fast UI preview. Run the strict macro QAOA mode for full QUBO-to-Ising statevector optimization."
        artifact_command = "py -3.11 strict_macro_quantum_v10.py --optimizer-mode qaoa"
        convergence = [
            {
                "cycle": cycle,
                "score": round(0.36 + math.log1p(cycle) * 0.118, 4),
                "loss": round(0.72 / (cycle + 1), 4),
            }
            for cycle in range(1, 9)
        ]

    weights = normalized_weights(raw_scores)
    allocations = []
    for index, asset in enumerate(source_assets):
        allocation = weights[index]
        allocations.append(
            {
                "ticker": asset["ticker"],
                "name": asset["name"],
                "weight": round(allocation, 6),
                "paperCapital": round(allocation * 500000, 2),
                "expectedReturn": asset["expected_return"],
                "volatility": asset["volatility"],
            }
        )

    expected_return = sum(item["weight"] * item["expectedReturn"] for item in allocations)
    risk = sum((item["weight"] * item["volatility"]) ** 2 for item in allocations) ** 0.5
    score = expected_return / (risk + 1e-6)
    return {
        "mode": normalized_mode,
        "label": label,
        "backend": backend,
        "description": description,
        "artifactCommand": artifact_command,
        "summary": {
            "paperCapital": 500000,
            "expectedReturn": round(expected_return, 4),
            "risk": round(risk, 4),
            "score": round(score, 4),
            "adviceBoundary": "Paper research output only. Not live trading advice.",
        },
        "allocations": allocations,
        "convergence": convergence,
    }


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 240_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 240_000)
    return hmac.compare_digest(digest.hex(), expected)


def create_jwt(user: dict) -> str:
    now = utc_now()
    expires_at = now + timedelta(seconds=access_token_max_age())
    return jwt.encode(
        {
            "sub": str(user["id"]),
            "email": user["email"],
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        },
        jwt_secret(),
        algorithm="HS256",
    )


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def access_cookie_header(token: str) -> str:
    secure = "; Secure" if cookie_secure() else ""
    return f"access_token={token}; Path=/; Max-Age={access_token_max_age()}; HttpOnly; SameSite=Lax{secure}"


def clear_cookie_header() -> str:
    secure = "; Secure" if cookie_secure() else ""
    return f"access_token=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax{secure}"


def load_seed_assets() -> list[tuple[str, str, float, float, float, float]]:
    if not SEED_CSV.exists():
        return DEFAULT_ASSETS

    rows = []
    with SEED_CSV.open("r", newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            try:
                rows.append(
                    (
                        row["ticker"],
                        row.get("name") or row["ticker"],
                        float(row["target_weight"]),
                        float(row["paper_cash"]),
                        float(row.get("expected_return_input", 0.0)),
                        float(row.get("volatility_input", 0.0)),
                    )
                )
            except (KeyError, ValueError):
                continue
    return rows or DEFAULT_ASSETS


def summarize_assets(assets: list[dict]) -> dict[str, float | int]:
    total_cash = sum(float(asset["paper_cash"]) for asset in assets)
    weighted_return = sum(float(asset["target_weight"]) * float(asset["expected_return"]) for asset in assets)
    weighted_risk = sum((float(asset["target_weight"]) * float(asset["volatility"])) ** 2 for asset in assets) ** 0.5
    return {
        "totalCash": round(total_cash, 2),
        "weightedReturn": round(weighted_return, 4),
        "weightedRisk": round(weighted_risk, 4),
        "assetCount": len(assets),
    }


def clean_status(value: str) -> str:
    allowed = {"research", "ready", "applied", "follow_up", "approved", "denied", "archived"}
    normalized = str(value or "research").strip().lower().replace(" ", "_").replace("-", "_")
    return normalized if normalized in allowed else "research"


def parse_deadline(value) -> date | None:
    if value in {None, ""}:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError("deadline must use YYYY-MM-DD, MM/DD/YYYY, or MM/DD/YY")


def grant_payload(payload: dict) -> dict:
    grant_name = str(payload.get("grantName") or payload.get("grant_name") or "").strip()
    if not grant_name:
        raise ValueError("grantName is required")

    try:
        funding_amount = float(payload.get("fundingAmount", payload.get("funding_amount", 0)))
    except (TypeError, ValueError) as exc:
        raise ValueError("fundingAmount must be a number") from exc
    if funding_amount < 0:
        raise ValueError("fundingAmount must be non-negative")

    try:
        difficulty = int(payload.get("applicationDifficulty", payload.get("application_difficulty", 3)))
    except (TypeError, ValueError) as exc:
        raise ValueError("applicationDifficulty must be an integer from 1 to 5") from exc
    if not 1 <= difficulty <= 5:
        raise ValueError("applicationDifficulty must be between 1 and 5")

    deadline = parse_deadline(payload.get("deadline"))
    status = clean_status(payload.get("status", "research"))
    priority_score = calculate_grant_priority(
        funding_amount=funding_amount,
        deadline=deadline,
        application_difficulty=difficulty,
        status=status,
    )
    return {
        "grant_name": grant_name,
        "funding_amount": funding_amount,
        "deadline": deadline,
        "application_difficulty": difficulty,
        "priority_score": priority_score,
        "status": status,
    }


def clean_housing_status(value: str) -> str:
    allowed = {"open", "requested", "scheduled", "resolved", "closed", "escalated"}
    normalized = str(value or "open").strip().lower().replace(" ", "_").replace("-", "_")
    return normalized if normalized in allowed else "open"


def housing_payload(payload: dict) -> dict:
    category = str(payload.get("category", "")).strip()
    description = str(payload.get("description", "")).strip()
    area_location = str(payload.get("areaLocation") or payload.get("area_location") or "").strip()
    if not category:
        raise ValueError("category is required")
    if not description:
        raise ValueError("description is required")
    if not area_location:
        raise ValueError("areaLocation is required")

    request_date = parse_deadline(payload.get("requestDate") or payload.get("request_date"))
    if request_date is None:
        raise ValueError("requestDate is required")
    resolve_date = parse_deadline(payload.get("resolveDate") or payload.get("resolve_date"))
    if resolve_date and resolve_date < request_date:
        raise ValueError("resolveDate cannot be before requestDate")

    try:
        severity = int(payload.get("severityLevel", payload.get("severity_level", 5)))
    except (TypeError, ValueError) as exc:
        raise ValueError("severityLevel must be an integer from 1 to 10") from exc
    if not 1 <= severity <= 10:
        raise ValueError("severityLevel must be between 1 and 10")

    status = clean_housing_status(payload.get("status", "open"))
    if resolve_date and status not in {"resolved", "closed"}:
        status = "resolved"
    return {
        "category": category,
        "description": description,
        "area_location": area_location,
        "request_date": request_date,
        "resolve_date": resolve_date,
        "severity_level": severity,
        "status": status,
    }


def days_unresolved(incident: dict) -> int:
    request_date = incident["request_date"]
    if isinstance(request_date, str):
        request_date = datetime.strptime(request_date[:10], "%Y-%m-%d").date()
    resolve_date = incident.get("resolve_date")
    if resolve_date:
        if isinstance(resolve_date, str):
            resolve_date = datetime.strptime(resolve_date[:10], "%Y-%m-%d").date()
        return max((resolve_date - request_date).days, 0)
    return max((date.today() - request_date).days, 0)


def housing_violation_flag(incident: dict) -> str:
    if incident["status"] in {"resolved", "closed"}:
        return "resolved"
    days = days_unresolved(incident)
    severity = int(incident["severity_level"])
    if severity >= 9 and days >= 1:
        return "critical_overdue"
    if severity >= 7 and days >= 3:
        return "urgent_overdue"
    if severity >= 5 and days >= 7:
        return "standard_overdue"
    if days >= 30:
        return "long_running"
    return "tracking"


def enrich_housing_incident(incident: dict) -> dict:
    return {
        **incident,
        "days_unresolved": days_unresolved(incident),
        "violation_flag": housing_violation_flag(incident),
    }


def inventory_payload(payload: dict) -> dict:
    item_name = str(payload.get("itemName") or payload.get("item_name") or "").strip()
    category = str(payload.get("category", "")).strip() or "General"
    notes = str(payload.get("notes", "")).strip()
    if not item_name:
        raise ValueError("itemName is required")

    try:
        estimated_market_value = float(payload.get("estimatedMarketValue", payload.get("estimated_market_value", 0)))
    except (TypeError, ValueError) as exc:
        raise ValueError("estimatedMarketValue must be a number") from exc
    if estimated_market_value < 0:
        raise ValueError("estimatedMarketValue must be non-negative")

    try:
        quantity = int(payload.get("quantity", 1))
    except (TypeError, ValueError) as exc:
        raise ValueError("quantity must be a positive integer") from exc
    if quantity <= 0:
        raise ValueError("quantity must be a positive integer")

    return {
        "item_name": item_name,
        "category": category,
        "estimated_market_value": estimated_market_value,
        "quantity": quantity,
        "notes": notes,
    }


def enrich_inventory_item(item: dict) -> dict:
    return {
        **item,
        "total_estimated_value": round(float(item["estimated_market_value"]) * int(item["quantity"]), 2),
    }


def clean_transaction_stage(value: str) -> str:
    allowed = {"listing", "under_contract", "closing", "closed"}
    normalized = str(value or "listing").strip().lower().replace(" ", "_").replace("-", "_")
    return normalized if normalized in allowed else "listing"


def listing_status_for_stage(stage: str) -> str:
    if stage == "closed":
        return "closed"
    if stage in {"under_contract", "closing"}:
        return "pending"
    return "active"


def transaction_payload(payload: dict) -> dict:
    address_street = str(payload.get("addressStreet") or payload.get("address_street") or "").strip()
    address_city = str(payload.get("addressCity") or payload.get("address_city") or "").strip()
    address_state = str(payload.get("addressState") or payload.get("address_state") or "").strip()
    address_zip = str(payload.get("addressZip") or payload.get("address_zip") or "").strip()
    buyer_name = str(payload.get("buyerName") or payload.get("buyer_name") or "Client file").strip()
    escrow_company = str(payload.get("escrowCompany") or payload.get("escrow_company") or "Pending offer").strip()
    if not all([address_street, address_city, address_state, address_zip]):
        raise ValueError("addressStreet, addressCity, addressState, and addressZip are required")

    try:
        price = float(payload.get("price", payload.get("contractPrice", payload.get("contract_price", 0))))
    except (TypeError, ValueError) as exc:
        raise ValueError("price must be a number") from exc
    if price < 0:
        raise ValueError("price must be non-negative")

    try:
        earnest_money = float(payload.get("earnestMoney", payload.get("earnest_money_amount", 0)))
    except (TypeError, ValueError) as exc:
        raise ValueError("earnestMoney must be a number") from exc
    if earnest_money < 0:
        raise ValueError("earnestMoney must be non-negative")

    target_closing_date = parse_deadline(payload.get("targetClosingDate") or payload.get("target_closing_date"))
    if target_closing_date is None:
        raise ValueError("targetClosingDate is required")

    milestones = []
    for item in payload.get("milestones", []):
        milestone_name = str(item.get("name") or item.get("milestoneName") or item.get("milestone_name") or "").strip()
        due_date = parse_deadline(item.get("dueDate") or item.get("due_date"))
        if not milestone_name or due_date is None:
            continue
        milestones.append(
            (
                milestone_name,
                due_date,
                None,
                bool(item.get("critical", item.get("is_critical_drop_dead", True))),
                str(item.get("notes", "")).strip(),
            )
        )

    return {
        "address_street": address_street,
        "address_city": address_city,
        "address_state": address_state,
        "address_zip": address_zip,
        "price": price,
        "buyer_name": buyer_name,
        "escrow_company": escrow_company,
        "earnest_money": earnest_money,
        "target_closing_date": target_closing_date,
        "stage": clean_transaction_stage(payload.get("stage", "listing")),
        "milestones": milestones,
    }


def shift_date(days: int) -> date:
    return date.today() + timedelta(days=days)


def transaction_milestone_risk(milestone: dict) -> str:
    if milestone.get("completed_at"):
        return "complete"
    due_date = milestone["due_date"]
    if isinstance(due_date, str):
        due_date = datetime.strptime(due_date[:10], "%Y-%m-%d").date()
    days = (due_date - date.today()).days
    if days < 0:
        return "breach"
    if milestone["is_critical_drop_dead"] and days <= 2:
        return "critical"
    if days <= 7:
        return "watch"
    return "clear"


def shape_transaction_rows(rows: list[dict]) -> list[dict]:
    deals: dict[int, dict] = {}
    for row in rows:
        transaction_id = int(row["transaction_id"])
        deal = deals.setdefault(
            transaction_id,
            {
                "id": f"TX-{transaction_id}",
                "transactionId": transaction_id,
                "listingId": int(row["listing_id"]),
                "stage": row["transaction_status"],
                "address": row["address_street"],
                "city": row["address_city"],
                "state": row["address_state"],
                "zip": row["address_zip"],
                "price": float(row["contract_price"]),
                "listingPrice": float(row["listing_price"]),
                "agent": row["agent_name"],
                "client": row["buyer_name"],
                "escrow": row["escrow_company"],
                "earnestMoney": float(row["earnest_money_amount"]),
                "closingDate": row["target_closing_date"],
                "milestones": [],
            },
        )
        if row.get("milestone_id"):
            milestone = {
                "id": int(row["milestone_id"]),
                "name": row["milestone_name"],
                "dueDate": row["due_date"],
                "completed": bool(row["completed_at"]),
                "completedAt": row["completed_at"],
                "critical": bool(row["is_critical_drop_dead"]),
                "notes": row["notes"],
            }
            milestone["risk"] = transaction_milestone_risk(
                {
                    "due_date": milestone["dueDate"],
                    "completed_at": milestone["completedAt"],
                    "is_critical_drop_dead": milestone["critical"],
                }
            )
            deal["milestones"].append(milestone)
    return list(deals.values())


def parse_stripe_signature(header: str) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for part in header.split(","):
        key, _, value = part.partition("=")
        if key and value:
            parsed.setdefault(key.strip(), []).append(value.strip())
    return parsed


def verify_stripe_signature(payload: bytes, header: str, secret: str, tolerance_seconds: int = 300) -> bool:
    parsed = parse_stripe_signature(header)
    timestamps = parsed.get("t", [])
    signatures = parsed.get("v1", [])
    if not timestamps or not signatures:
        return False
    try:
        timestamp = int(timestamps[0])
    except ValueError:
        return False
    if abs(int(time.time()) - timestamp) > tolerance_seconds:
        return False
    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, signature) for signature in signatures)


def unix_to_datetime(value) -> datetime | None:
    if value in {None, ""}:
        return None
    try:
        return datetime.fromtimestamp(int(value), timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def metadata_user_id(obj: dict) -> int | None:
    metadata = obj.get("metadata") or {}
    raw_user_id = metadata.get("user_id") or metadata.get("tenant_id") or obj.get("client_reference_id")
    try:
        return int(raw_user_id) if raw_user_id not in {None, ""} else None
    except (TypeError, ValueError):
        return None


def stripe_tier(obj: dict) -> str:
    metadata = obj.get("metadata") or {}
    if metadata.get("tier"):
        return str(metadata["tier"]).strip().lower() or "free"
    if obj.get("mode") == "subscription":
        return "subscription"
    return "free"


def upsert_billing_account(cursor: RealDictCursor, *, customer_id: str, status: str, tier: str, user_id: int | None, current_period_end: datetime | None) -> None:
    cursor.execute(
        """
        INSERT INTO billing_accounts
            (user_id, stripe_customer_id, subscription_tier, account_status, current_period_end)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (stripe_customer_id) DO UPDATE SET
            user_id = COALESCE(EXCLUDED.user_id, billing_accounts.user_id),
            subscription_tier = EXCLUDED.subscription_tier,
            account_status = EXCLUDED.account_status,
            current_period_end = EXCLUDED.current_period_end,
            updated_at = now()
        """,
        (user_id, customer_id, tier, status, current_period_end),
    )


def process_stripe_event(cursor: RealDictCursor, event: dict) -> str:
    event_id = str(event.get("id", "")).strip()
    event_type = str(event.get("type", "")).strip()
    obj = ((event.get("data") or {}).get("object") or {})
    if not event_id or not event_type or not isinstance(obj, dict):
        raise ValueError("Stripe event payload is missing id, type, or data.object")

    cursor.execute(
        """
        INSERT INTO stripe_webhook_events (event_id, event_type, payload_json)
        VALUES (%s, %s, %s::jsonb)
        ON CONFLICT (event_id) DO NOTHING
        RETURNING event_id
        """,
        (event_id, event_type, json.dumps(event)),
    )
    inserted = cursor.fetchone()
    if not inserted:
        return "duplicate"

    if event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
        customer_id = str(obj.get("customer", "")).strip()
        if customer_id:
            status = "inactive" if event_type.endswith(".deleted") else str(obj.get("status", "inactive")).strip().lower()
            upsert_billing_account(
                cursor,
                customer_id=customer_id,
                status=status,
                tier=stripe_tier(obj),
                user_id=metadata_user_id(obj),
                current_period_end=unix_to_datetime(obj.get("current_period_end")),
            )
    elif event_type == "checkout.session.completed":
        customer_id = str(obj.get("customer", "")).strip()
        if customer_id:
            upsert_billing_account(
                cursor,
                customer_id=customer_id,
                status="active",
                tier=stripe_tier(obj),
                user_id=metadata_user_id(obj),
                current_period_end=unix_to_datetime(obj.get("expires_at")),
            )
    elif event_type in {"invoice.payment_failed", "customer.subscription.paused"}:
        customer_id = str(obj.get("customer", "")).strip()
        if customer_id:
            cursor.execute(
                """
                UPDATE billing_accounts
                SET account_status = %s,
                    updated_at = now()
                WHERE stripe_customer_id = %s
                """,
                ("past_due" if event_type == "invoice.payment_failed" else "paused", customer_id),
            )

    cursor.execute("UPDATE stripe_webhook_events SET processed_at = now() WHERE event_id = %s", (event_id,))
    return "processed"


class StripeCheckoutError(RuntimeError):
    def __init__(self, message: str, status: int = HTTPStatus.BAD_GATEWAY):
        super().__init__(message)
        self.status = status


def checkout_tier(payload: dict) -> str:
    tier = str(payload.get("tier", "starter")).strip().lower().replace(" ", "_").replace("-", "_")
    if tier not in {"starter", "pro", "enterprise"}:
        raise ValueError("tier must be starter, pro, or enterprise")
    return tier


def create_stripe_checkout_session(user: dict, tier: str) -> dict:
    config = settings()
    if config.stripe_secret_key is None:
        raise StripeCheckoutError("Stripe secret key is not configured", HTTPStatus.SERVICE_UNAVAILABLE)

    price_id = config.stripe_price_map.get(tier)
    if not price_id:
        raise StripeCheckoutError(f"Stripe price is not configured for tier '{tier}'", HTTPStatus.SERVICE_UNAVAILABLE)

    form = {
        "mode": "subscription",
        "success_url": config.stripe_success_url,
        "cancel_url": config.stripe_cancel_url,
        "customer_email": user["email"],
        "client_reference_id": str(user["id"]),
        "line_items[0][price]": price_id,
        "line_items[0][quantity]": "1",
        "metadata[user_id]": str(user["id"]),
        "metadata[tier]": tier,
        "subscription_data[metadata][user_id]": str(user["id"]),
        "subscription_data[metadata][tier]": tier,
        "allow_promotion_codes": "true",
    }
    request = Request(
        STRIPE_CHECKOUT_ENDPOINT,
        data=urlencode(form).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.stripe_secret_key.get_secret_value()}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            message = (payload.get("error") or {}).get("message") or "Stripe Checkout request failed"
        except (json.JSONDecodeError, UnicodeDecodeError):
            message = "Stripe Checkout request failed"
        raise StripeCheckoutError(message, HTTPStatus.BAD_GATEWAY) from exc
    except (URLError, TimeoutError) as exc:
        raise StripeCheckoutError("Stripe Checkout request could not reach Stripe", HTTPStatus.BAD_GATEWAY) from exc


def calculate_grant_priority(
    funding_amount: float,
    deadline: date | None,
    application_difficulty: int,
    status: str,
) -> float:
    score = min(funding_amount / 1000.0, 65.0)
    if deadline is None:
        score -= 4.0
    else:
        days_left = (deadline - date.today()).days
        if days_left < 0:
            score -= 80.0
        elif days_left <= 7:
            score += 24.0
        elif days_left <= 30:
            score += 16.0
        elif days_left <= 60:
            score += 9.0
        else:
            score += 3.0
    score -= application_difficulty * 3.0
    score += {
        "ready": 10.0,
        "research": 3.0,
        "follow_up": 2.0,
        "applied": -10.0,
        "approved": -25.0,
        "denied": -45.0,
        "archived": -60.0,
    }.get(status, 0.0)
    return round(score, 2)


def seed_user_assets(cursor: RealDictCursor, user_id: int) -> None:
    now = utc_now()
    seed_rows = [(user_id, *asset, now) for asset in load_seed_assets()]
    execute_values(
        cursor,
        """
        INSERT INTO portfolio_assets
            (user_id, ticker, name, target_weight, paper_cash, expected_return, volatility, updated_at)
        VALUES %s
        ON CONFLICT (user_id, ticker) DO UPDATE SET
            name = EXCLUDED.name,
            target_weight = EXCLUDED.target_weight,
            paper_cash = EXCLUDED.paper_cash,
            expected_return = EXCLUDED.expected_return,
            volatility = EXCLUDED.volatility,
            updated_at = EXCLUDED.updated_at
        """,
        seed_rows,
    )

    assets = [
        {
            "target_weight": row[3],
            "paper_cash": row[4],
            "expected_return": row[5],
            "volatility": row[6],
        }
        for row in seed_rows
    ]
    summary = summarize_assets(assets)
    cursor.execute(
        """
        INSERT INTO portfolio_history
            (user_id, source, total_cash, weighted_return, weighted_risk, asset_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            "registration_seed",
            summary["totalCash"],
            summary["weightedReturn"],
            summary["weightedRisk"],
            summary["assetCount"],
        ),
    )

    run_id = f"seed-{user_id}-{int(now.timestamp())}"
    execute_values(
        cursor,
        """
        INSERT INTO quantum_telemetry_metrics
            (user_id, run_id, backend, metric_name, metric_value)
        VALUES %s
        """,
        [
            (user_id, run_id, "local_seed", "weighted_return", summary["weightedReturn"]),
            (user_id, run_id, "local_seed", "weighted_risk", summary["weightedRisk"]),
            (user_id, run_id, "local_seed", "asset_count", summary["assetCount"]),
        ],
    )


def seed_user_transactions(cursor: RealDictCursor, user_id: int) -> None:
    cursor.execute("SELECT COUNT(*) AS count FROM real_estate_transactions WHERE tenant_id = %s", (user_id,))
    if int(cursor.fetchone()["count"]) > 0:
        return

    seed_deals = [
        {
            "stage": "listing",
            "address": ("418 Harbor View Lane", "Charleston", "SC", "29401"),
            "price": 485000,
            "buyer_name": "Seller file",
            "escrow": "Pending offer",
            "earnest": 0,
            "closing": shift_date(42),
            "milestones": [
                ("Seller disclosure packet", shift_date(2), None, True, "Upload signed disclosure before offer review."),
                ("MLS photo review", shift_date(4), None, False, "Confirm image order and feature sheet."),
                ("Offer review window", shift_date(9), None, True, "Calendar seller response deadline."),
            ],
        },
        {
            "stage": "under_contract",
            "address": ("92 Cedar Mill Court", "Raleigh", "NC", "27601"),
            "price": 612500,
            "buyer_name": "Buyer file",
            "escrow": "Atlantic Title",
            "earnest": 18500,
            "closing": shift_date(28),
            "milestones": [
                ("Inspection contingency", shift_date(1), None, True, "Deposit exposure begins if missed."),
                ("Appraisal ordered", shift_date(5), None, True, "Confirm lender order and access."),
                ("Loan approval deadline", shift_date(13), None, True, "Financing condition drop-dead date."),
            ],
        },
        {
            "stage": "under_contract",
            "address": ("733 Market Row", "Atlanta", "GA", "30303"),
            "price": 748000,
            "buyer_name": "Investor file",
            "escrow": "Secure Escrow Co.",
            "earnest": 25000,
            "closing": shift_date(18),
            "milestones": [
                ("HOA document review", shift_date(-1), None, True, "Review period is past due."),
                ("Financing condition", shift_date(6), None, True, "Track lender commitment."),
                ("Final walkthrough", shift_date(16), None, False, "Schedule before closing appointment."),
            ],
        },
        {
            "stage": "closing",
            "address": ("1509 Ridgecrest Avenue", "Nashville", "TN", "37203"),
            "price": 524900,
            "buyer_name": "Relocation file",
            "escrow": "Keystone Settlement",
            "earnest": 16000,
            "closing": shift_date(5),
            "milestones": [
                ("Clear to close", shift_date(0), None, True, "Must clear before wire package."),
                ("Wire instructions verified", shift_date(2), None, True, "Verify out-of-band with settlement office."),
                ("Closing appointment", shift_date(5), None, True, "Final signature window."),
            ],
        },
        {
            "stage": "closed",
            "address": ("21 Maple Station Drive", "Charlotte", "NC", "28202"),
            "price": 389000,
            "buyer_name": "Closed buyer file",
            "escrow": "Closed",
            "earnest": 12000,
            "closing": shift_date(-8),
            "milestones": [
                ("Inspection contingency", shift_date(-27), utc_now(), True, "Satisfied."),
                ("Loan approval deadline", shift_date(-18), utc_now(), True, "Satisfied."),
                ("Recorded closing", shift_date(-8), utc_now(), True, "Recorded."),
            ],
        },
    ]

    for deal in seed_deals:
        street, city, state, zip_code = deal["address"]
        cursor.execute(
            """
            INSERT INTO real_estate_listings
                (tenant_id, agent_id, address_street, address_city, address_state,
                 address_zip, price, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING listing_id
            """,
            (
                user_id,
                user_id,
                street,
                city,
                state,
                zip_code,
                deal["price"],
                "closed" if deal["stage"] == "closed" else "pending" if deal["stage"] != "listing" else "active",
            ),
        )
        listing_id = cursor.fetchone()["listing_id"]
        cursor.execute(
            """
            INSERT INTO real_estate_transactions
                (tenant_id, listing_id, agent_id, buyer_name, contract_price,
                 escrow_company, earnest_money_amount, target_closing_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING transaction_id
            """,
            (
                user_id,
                listing_id,
                user_id,
                deal["buyer_name"],
                deal["price"],
                deal["escrow"],
                deal["earnest"],
                deal["closing"],
                deal["stage"],
            ),
        )
        transaction_id = cursor.fetchone()["transaction_id"]
        execute_values(
            cursor,
            """
            INSERT INTO transaction_milestones
                (transaction_id, milestone_name, due_date, completed_at, is_critical_drop_dead, notes)
            VALUES %s
            """,
            [
                (transaction_id, name, due_date, completed_at, critical, notes)
                for name, due_date, completed_at, critical, notes in deal["milestones"]
            ],
        )


class ApiHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def request_id(self) -> str:
        existing = getattr(self, "_request_id", None)
        if existing:
            return existing

        supplied = self.headers.get("X-Request-ID") or self.headers.get("X-Correlation-ID")
        if supplied:
            cleaned = "".join(ch for ch in supplied.strip() if ch.isalnum() or ch in {"-", "_"})
            request_id = cleaned[:80] if cleaned else ""
        else:
            request_id = ""
        if not request_id:
            request_id = f"req-{uuid.uuid4().hex[:12]}"
        self._request_id = request_id
        return request_id

    def log_event(self, event: str, **fields) -> None:
        log_event(event, request_id=self.request_id(), **fields)

    def client_ip(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
        return self.client_address[0]

    def cors_headers(self) -> dict[str, str]:
        origin = self.headers.get("Origin", "").rstrip("/")
        if origin and origin not in allowed_origins():
            return {}
        headers = {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Max-Age": "600",
        }
        if origin:
            headers["Access-Control-Allow-Origin"] = origin
        return headers

    def send_json(self, status: int, payload: dict, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        merged_headers = {"X-Request-ID": self.request_id(), **self.cors_headers(), **(headers or {})}
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in merged_headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)
        self.log_event(
            "api_response",
            method=self.command,
            path=urlparse(self.path).path,
            status=int(status),
            ip=self.client_ip(),
        )

    def send_openapi_spec(self) -> None:
        if not OPENAPI_SPEC.exists():
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "OpenAPI contract not found"})
            return
        try:
            payload = json.loads(OPENAPI_SPEC.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "OpenAPI contract is invalid JSON"})
            return
        self.send_json(HTTPStatus.OK, payload)

    def send_static_file(self, path: str) -> None:
        if not STATIC_ROOT.exists():
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Dashboard static assets not built"})
            return

        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        target = (STATIC_ROOT / relative).resolve()
        static_root = STATIC_ROOT.resolve()
        if not str(target).startswith(str(static_root)) or not target.exists() or not target.is_file():
            target = static_root / "index.html"
        if not target.exists():
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Dashboard entrypoint not found"})
            return

        body = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-ID", self.request_id())
        for key, value in self.cors_headers().items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)
        self.log_event("static_response", path=urlparse(self.path).path, status=200, ip=self.client_ip())

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin", "").rstrip("/")
        if origin and origin not in allowed_origins():
            self.send_json(HTTPStatus.FORBIDDEN, {"error": "Origin not allowed"})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("X-Request-ID", self.request_id())
        for key, value in self.cors_headers().items():
            self.send_header(key, value)
        self.end_headers()

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def read_json(self) -> dict:
        body = self.read_body()
        if not body:
            return {}
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def cookie_token(self) -> str | None:
        raw = self.headers.get("Cookie", "")
        for part in raw.split(";"):
            key, _, value = part.strip().partition("=")
            if key == "access_token" and value:
                return value
        auth = self.headers.get("Authorization", "")
        prefix = "Bearer "
        if auth.startswith(prefix):
            return auth[len(prefix) :].strip()
        return None

    def rate_limit(self) -> bool:
        path = urlparse(self.path).path
        if path == "/api/health":
            return True
        is_auth = path in {"/api/login", "/api/register"}
        config = settings()
        limit = config.rate_limit_auth_per_minute if is_auth else config.rate_limit_api_per_minute
        now = time.time()
        window_start = now - 60
        key = f"{self.client_ip()}:{path}"
        with RATE_LIMIT_LOCK:
            bucket = [stamp for stamp in RATE_LIMIT_BUCKETS.get(key, []) if stamp >= window_start]
            if len(bucket) >= limit:
                RATE_LIMIT_BUCKETS[key] = bucket
                self.log_event("rate_limit_block", path=path, ip=self.client_ip(), limit=limit)
                return False
            bucket.append(now)
            RATE_LIMIT_BUCKETS[key] = bucket
        return True

    def handle_stripe_webhook(self) -> None:
        webhook_secret = settings().stripe_webhook_secret
        if webhook_secret is None:
            self.send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Stripe webhook is not configured"})
            return

        raw_body = self.read_body()
        signature = self.headers.get("Stripe-Signature", "")
        if not verify_stripe_signature(raw_body, signature, webhook_secret.get_secret_value()):
            self.log_event("stripe_webhook_signature_rejected", ip=self.client_ip())
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid Stripe signature"})
            return

        try:
            event = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid Stripe event JSON"})
            return

        try:
            with db_cursor(commit=True) as cursor:
                outcome = process_stripe_event(cursor, event)
        except ValueError as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        self.log_event("stripe_webhook_processed", event_id=event.get("id"), event_type=event.get("type"), outcome=outcome, ip=self.client_ip())
        self.send_json(HTTPStatus.OK, {"ok": True, "outcome": outcome})

    def current_user(self) -> dict | None:
        if local_demo_mode():
            return DEMO_USER
        token = self.cookie_token()
        if not token:
            return None
        claims = decode_jwt(token)
        if not claims:
            return None
        with db_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM user_profiles WHERE id = %s AND email = %s",
                (claims.get("sub"), claims.get("email")),
            )
            return cursor.fetchone()

    def require_user(self) -> dict | None:
        user = self.current_user()
        if user is None:
            self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "Authentication required"})
        return user

    def grant_id_from_path(self, path: str) -> int | None:
        parts = [part for part in path.split("/") if part]
        if len(parts) != 3 or parts[0] != "api" or parts[1] != "grants":
            return None
        try:
            return int(parts[2])
        except ValueError:
            return None

    def housing_id_from_path(self, path: str) -> int | None:
        parts = [part for part in path.split("/") if part]
        if len(parts) != 3 or parts[0] != "api" or parts[1] != "housing":
            return None
        try:
            return int(parts[2])
        except ValueError:
            return None

    def inventory_id_from_path(self, path: str) -> int | None:
        parts = [part for part in path.split("/") if part]
        if len(parts) != 3 or parts[0] != "api" or parts[1] != "inventory":
            return None
        try:
            return int(parts[2])
        except ValueError:
            return None

    def transaction_stage_from_path(self, path: str) -> int | None:
        parts = [part for part in path.split("/") if part]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "transactions" or parts[3] != "stage":
            return None
        raw_id = parts[2].upper().removeprefix("TX-")
        try:
            return int(raw_id)
        except ValueError:
            return None

    def send_demo_session(self) -> None:
        self.send_json(
            HTTPStatus.OK,
            {"user": {"email": DEMO_USER["email"], "displayName": DEMO_USER["display_name"]}},
            {"Set-Cookie": access_cookie_header(DEMO_USER)},
        )

    def handle_demo_get(self, path: str) -> bool:
        if path == "/api/health":
            self.send_json(HTTPStatus.OK, {"ok": True, "database": "demo_sqlite", "auth": "demo_jwt"})
            return True
        if path == "/api/me":
            self.send_json(HTTPStatus.OK, {"user": {"email": DEMO_USER["email"], "displayName": DEMO_USER["display_name"]}})
            return True
        if path == "/api/portfolio":
            self.log_event("demo_portfolio_payload", user_id=DEMO_USER["id"], ip=self.client_ip())
            self.send_json(HTTPStatus.OK, demo_portfolio_payload())
            return True
        if path == "/api/grants":
            self.log_event("demo_grant_ledger_list", user_id=DEMO_USER["id"], count=len(DEMO_DB["grants"]), ip=self.client_ip())
            self.send_json(HTTPStatus.OK, demo_grants_payload())
            return True
        if path == "/api/housing":
            self.log_event("demo_housing_incident_list", user_id=DEMO_USER["id"], count=len(DEMO_DB["housing"]), ip=self.client_ip())
            self.send_json(HTTPStatus.OK, demo_housing_payload())
            return True
        if path == "/api/inventory":
            self.log_event("demo_inventory_list", user_id=DEMO_USER["id"], count=len(DEMO_DB["inventory"]), ip=self.client_ip())
            self.send_json(HTTPStatus.OK, demo_inventory_payload())
            return True
        if path == "/api/transactions":
            self.log_event("demo_transaction_pipeline_list", user_id=DEMO_USER["id"], count=len(DEMO_DB["transactions"]), ip=self.client_ip())
            self.send_json(HTTPStatus.OK, demo_transactions_payload())
            return True
        return False

    def handle_demo_post(self, path: str, payload: dict) -> bool:
        if path in {"/api/register", "/api/login"}:
            self.log_event("demo_login", user_id=DEMO_USER["id"], ip=self.client_ip())
            self.send_demo_session()
            return True
        if path == "/api/logout":
            self.send_json(HTTPStatus.OK, {"ok": True}, {"Set-Cookie": clear_cookie_header()})
            return True
        if path == "/api/stripe/checkout":
            self.send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Stripe Checkout is disabled in local demo mode."})
            return True
        if path == "/api/grants":
            try:
                values = grant_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return True
            with DEMO_LOCK:
                grant = {
                    "id": next_demo_id("grants", "id"),
                    **values,
                    "created_at": utc_now(),
                    "updated_at": utc_now(),
                }
                DEMO_DB["grants"].append(grant)
                save_demo_memory_to_sqlite()
            self.send_json(HTTPStatus.CREATED, {"grant": grant})
            return True
        if path == "/api/housing":
            try:
                values = housing_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return True
            with DEMO_LOCK:
                incident = enrich_housing_incident(
                    {
                        "incident_id": next_demo_id("housing", "incident_id"),
                        **values,
                        "created_at": utc_now(),
                        "updated_at": utc_now(),
                    }
                )
                DEMO_DB["housing"].append(incident)
                save_demo_memory_to_sqlite()
            self.send_json(HTTPStatus.CREATED, {"incident": incident})
            return True
        if path == "/api/inventory":
            try:
                values = inventory_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return True
            with DEMO_LOCK:
                item = enrich_inventory_item(
                    {
                        "item_id": next_demo_id("inventory", "item_id"),
                        **values,
                        "acquired_at": utc_now(),
                        "created_at": utc_now(),
                        "updated_at": utc_now(),
                    }
                )
                DEMO_DB["inventory"].append(item)
                save_demo_memory_to_sqlite()
            self.send_json(HTTPStatus.CREATED, {"item": item})
            return True
        if path == "/api/transactions":
            try:
                values = transaction_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return True
            with DEMO_LOCK:
                transaction_id = next_demo_id("transactions", "transactionId")
                milestones = []
                for index, (name, due_date, completed_at, critical, notes) in enumerate(values["milestones"], start=1):
                    milestone = {
                        "id": transaction_id * 100 + index,
                        "name": name,
                        "dueDate": due_date,
                        "completed": bool(completed_at),
                        "completedAt": completed_at,
                        "critical": critical,
                        "notes": notes,
                    }
                    milestone["risk"] = transaction_milestone_risk(
                        {
                            "due_date": due_date,
                            "completed_at": completed_at,
                            "is_critical_drop_dead": critical,
                        }
                    )
                    milestones.append(milestone)
                transaction = {
                    "id": f"TX-{transaction_id}",
                    "transactionId": transaction_id,
                    "listingId": transaction_id,
                    "stage": values["stage"],
                    "address": values["address_street"],
                    "city": values["address_city"],
                    "state": values["address_state"],
                    "zip": values["address_zip"],
                    "price": values["price"],
                    "listingPrice": values["price"],
                    "agent": DEMO_USER["display_name"],
                    "client": values["buyer_name"],
                    "escrow": values["escrow_company"],
                    "earnestMoney": values["earnest_money"],
                    "closingDate": values["target_closing_date"],
                    "milestones": milestones,
                }
                DEMO_DB["transactions"].append(transaction)
                save_demo_memory_to_sqlite()
            self.send_json(HTTPStatus.CREATED, {"ok": True, "transactionId": transaction_id})
            return True
        return False

    def handle_demo_put(self, path: str, payload: dict) -> bool:
        grant_id = self.grant_id_from_path(path)
        housing_id = self.housing_id_from_path(path)
        inventory_id = self.inventory_id_from_path(path)
        if grant_id is not None:
            try:
                values = grant_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return True
            with DEMO_LOCK:
                grant = next((item for item in DEMO_DB["grants"] if item["id"] == grant_id), None)
                if grant:
                    grant.update(values)
                    grant["updated_at"] = utc_now()
                    save_demo_memory_to_sqlite()
            if not grant:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "Grant not found"})
            else:
                self.send_json(HTTPStatus.OK, {"grant": grant})
            return True
        if housing_id is not None:
            try:
                values = housing_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return True
            with DEMO_LOCK:
                incident = next((item for item in DEMO_DB["housing"] if item["incident_id"] == housing_id), None)
                if incident:
                    incident.update(values)
                    incident["updated_at"] = utc_now()
                    incident = enrich_housing_incident(incident)
                    save_demo_memory_to_sqlite()
            if not incident:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "Housing incident not found"})
            else:
                self.send_json(HTTPStatus.OK, {"incident": incident})
            return True
        if inventory_id is not None:
            try:
                values = inventory_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return True
            with DEMO_LOCK:
                item = next((row for row in DEMO_DB["inventory"] if row["item_id"] == inventory_id), None)
                if item:
                    item.update(values)
                    item["updated_at"] = utc_now()
                    item = enrich_inventory_item(item)
                    save_demo_memory_to_sqlite()
            if not item:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "Inventory item not found"})
            else:
                self.send_json(HTTPStatus.OK, {"item": item})
            return True
        return False

    def handle_demo_patch(self, path: str, payload: dict) -> bool:
        transaction_id = self.transaction_stage_from_path(path)
        if transaction_id is None:
            return False
        stage = clean_transaction_stage(payload.get("stage", "listing"))
        with DEMO_LOCK:
            transaction = next((item for item in DEMO_DB["transactions"] if item["transactionId"] == transaction_id), None)
            if transaction:
                transaction["stage"] = stage
                save_demo_memory_to_sqlite()
        if not transaction:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Transaction not found"})
        else:
            self.log_event("demo_transaction_stage_updated", user_id=DEMO_USER["id"], transaction_id=transaction_id, stage=stage, ip=self.client_ip())
            self.send_json(HTTPStatus.OK, {"ok": True, "transactionId": transaction_id, "stage": stage})
        return True

    def handle_demo_delete(self, path: str) -> bool:
        targets = [
            ("grants", "id", self.grant_id_from_path(path), "Grant not found"),
            ("housing", "incident_id", self.housing_id_from_path(path), "Housing incident not found"),
            ("inventory", "item_id", self.inventory_id_from_path(path), "Inventory item not found"),
        ]
        for table, key, row_id, message in targets:
            if row_id is None:
                continue
            with DEMO_LOCK:
                before = len(DEMO_DB[table])
                DEMO_DB[table] = [row for row in DEMO_DB[table] if row[key] != row_id]
                deleted = len(DEMO_DB[table]) < before
                if deleted:
                    save_demo_memory_to_sqlite()
            if not deleted:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": message})
            else:
                self.send_json(HTTPStatus.OK, {"ok": True})
            return True
        return False

    def do_GET(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path == "/api/health":
            self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "database": "demo_sqlite" if local_demo_mode() else "postgresql",
                    "auth": "demo_jwt" if local_demo_mode() else "jwt",
                },
            )
            return

        if path in {"/openapi.json", "/api/openapi.json"}:
            self.send_openapi_spec()
            return

        if path == "/api/optimizer":
            mode = parse_qs(parsed_url.query).get("mode", ["classical"])[0]
            self.log_event("optimizer_payload", mode=mode, ip=self.client_ip())
            self.send_json(HTTPStatus.OK, optimizer_payload(mode))
            return

        if local_demo_mode() and self.handle_demo_get(path):
            return

        if path == "/api/me":
            user = self.current_user()
            if not user:
                self.send_json(HTTPStatus.OK, {"user": None})
                return
            self.send_json(
                HTTPStatus.OK,
                {"user": {"email": user["email"], "displayName": user["display_name"]}},
            )
            return

        if path == "/api/portfolio":
            user = self.require_user()
            if not user:
                return
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT ticker, name, target_weight, paper_cash, expected_return, volatility, updated_at
                    FROM portfolio_assets
                    WHERE user_id = %s
                    ORDER BY target_weight DESC
                    """,
                    (user["id"],),
                )
                assets = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT source, total_cash, weighted_return, weighted_risk, asset_count, created_at
                    FROM portfolio_history
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 10
                    """,
                    (user["id"],),
                )
                history = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT run_id, backend, metric_name, metric_value, created_at
                    FROM quantum_telemetry_metrics
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 25
                    """,
                    (user["id"],),
                )
                telemetry = cursor.fetchall()

            self.log_event("portfolio_payload", user_id=user["id"], asset_count=len(assets), ip=self.client_ip())
            self.send_json(
                HTTPStatus.OK,
                {
                    "summary": summarize_assets(assets),
                    "assets": assets,
                    "history": history,
                    "telemetry": telemetry,
                },
            )
            return

        if path == "/api/grants":
            user = self.require_user()
            if not user:
                return
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, grant_name, funding_amount, deadline, application_difficulty,
                           priority_score, status, created_at, updated_at
                    FROM grant_ledger
                    WHERE user_id = %s
                    ORDER BY priority_score DESC, deadline ASC NULLS LAST, funding_amount DESC
                    """,
                    (user["id"],),
                )
                grants = cursor.fetchall()
            active_grants = [grant for grant in grants if grant["status"] not in {"denied", "archived"}]
            total_funding = sum(float(grant["funding_amount"]) for grant in active_grants)
            self.log_event("grant_ledger_list", user_id=user["id"], count=len(grants), ip=self.client_ip())
            self.send_json(
                HTTPStatus.OK,
                {
                    "summary": {
                        "grantCount": len(grants),
                        "activeGrantCount": len(active_grants),
                        "totalFunding": round(total_funding, 2),
                        "topPriorityScore": float(grants[0]["priority_score"]) if grants else 0,
                    },
                    "grants": grants,
                },
            )
            return

        if path == "/api/housing":
            user = self.require_user()
            if not user:
                return
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT incident_id, category, description, area_location, request_date,
                           resolve_date, severity_level, status, created_at, updated_at
                    FROM housing_incidents
                    WHERE user_id = %s
                    ORDER BY
                        CASE WHEN status IN ('resolved', 'closed') THEN 1 ELSE 0 END,
                        severity_level DESC,
                        request_date DESC
                    """,
                    (user["id"],),
                )
                incidents = [enrich_housing_incident(row) for row in cursor.fetchall()]
            open_incidents = [item for item in incidents if item["status"] not in {"resolved", "closed"}]
            overdue_incidents = [item for item in incidents if item["violation_flag"] not in {"resolved", "tracking"}]
            self.log_event("housing_incident_list", user_id=user["id"], count=len(incidents), ip=self.client_ip())
            self.send_json(
                HTTPStatus.OK,
                {
                    "summary": {
                        "incidentCount": len(incidents),
                        "openIncidentCount": len(open_incidents),
                        "overdueCount": len(overdue_incidents),
                        "maxDaysUnresolved": max([item["days_unresolved"] for item in open_incidents], default=0),
                    },
                    "incidents": incidents,
                },
            )
            return

        if path == "/api/inventory":
            user = self.require_user()
            if not user:
                return
            with db_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT item_id, item_name, category, estimated_market_value, quantity,
                           notes, acquired_at, created_at, updated_at
                    FROM asset_inventory
                    WHERE user_id = %s
                    ORDER BY estimated_market_value * quantity DESC, acquired_at DESC
                    """,
                    (user["id"],),
                )
                items = [enrich_inventory_item(row) for row in cursor.fetchall()]
            total_value = sum(float(item["total_estimated_value"]) for item in items)
            categories = sorted({item["category"] for item in items})
            self.log_event("inventory_list", user_id=user["id"], count=len(items), ip=self.client_ip())
            self.send_json(
                HTTPStatus.OK,
                {
                    "summary": {
                        "itemCount": len(items),
                        "categoryCount": len(categories),
                        "totalEstimatedValue": round(total_value, 2),
                        "topItemValue": max([float(item["total_estimated_value"]) for item in items], default=0),
                    },
                    "items": items,
                },
            )
            return

        if path == "/api/transactions":
            user = self.require_user()
            if not user:
                return
            with db_cursor(commit=True) as cursor:
                seed_user_transactions(cursor, int(user["id"]))
                cursor.execute(
                    """
                    SELECT
                        t.transaction_id,
                        t.listing_id,
                        t.status AS transaction_status,
                        t.buyer_name,
                        t.contract_price,
                        t.escrow_company,
                        t.earnest_money_amount,
                        t.target_closing_date,
                        l.address_street,
                        l.address_city,
                        l.address_state,
                        l.address_zip,
                        l.price AS listing_price,
                        u.display_name AS agent_name,
                        m.milestone_id,
                        m.milestone_name,
                        m.due_date,
                        m.completed_at,
                        m.is_critical_drop_dead,
                        m.notes
                    FROM real_estate_transactions t
                    JOIN real_estate_listings l ON l.listing_id = t.listing_id
                    JOIN user_profiles u ON u.id = t.agent_id
                    LEFT JOIN transaction_milestones m ON m.transaction_id = t.transaction_id
                    WHERE t.tenant_id = %s
                    ORDER BY
                        CASE t.status
                            WHEN 'listing' THEN 1
                            WHEN 'under_contract' THEN 2
                            WHEN 'closing' THEN 3
                            WHEN 'closed' THEN 4
                            ELSE 5
                        END,
                        t.target_closing_date ASC,
                        m.due_date ASC
                    """,
                    (user["id"],),
                )
                deals = shape_transaction_rows(cursor.fetchall())
            active_deals = [deal for deal in deals if deal["stage"] != "closed"]
            all_milestones = [milestone for deal in deals for milestone in deal["milestones"]]
            due_this_week = [
                milestone
                for milestone in all_milestones
                if not milestone["completed"] and 0 <= (milestone["dueDate"] - date.today()).days <= 7
            ]
            breached = [milestone for milestone in all_milestones if milestone.get("risk") == "breach"]
            self.log_event("transaction_pipeline_list", user_id=user["id"], count=len(deals), ip=self.client_ip())
            self.send_json(
                HTTPStatus.OK,
                {
                    "summary": {
                        "activeDealCount": len(active_deals),
                        "activeDealValue": round(sum(float(deal["price"]) for deal in active_deals), 2),
                        "earnestExposure": round(sum(float(deal["earnestMoney"]) for deal in active_deals), 2),
                        "deadlineBreachCount": len(breached),
                        "dueThisWeekCount": len(due_this_week),
                    },
                    "deals": deals,
                },
            )
            return

        if not path.startswith("/api/"):
            self.send_static_file(path)
            return

        self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
        if path == "/api/stripe/webhook":
            self.handle_stripe_webhook()
            return

        payload = self.read_json()
        if local_demo_mode() and self.handle_demo_post(path, payload):
            return

        if path == "/api/register":
            email = str(payload.get("email", "")).strip().lower()
            display_name = str(payload.get("displayName", "")).strip() or "Portfolio User"
            password = str(payload.get("password", ""))
            if "@" not in email or len(password) < 8:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Use a valid email and an 8+ character password."})
                return
            try:
                with db_cursor(commit=True) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO user_profiles (email, display_name, password_hash)
                        VALUES (%s, %s, %s)
                        RETURNING id, email, display_name
                        """,
                        (email, display_name, hash_password(password)),
                    )
                    user = cursor.fetchone()
                    seed_user_assets(cursor, int(user["id"]))
                    seed_user_transactions(cursor, int(user["id"]))
            except errors.UniqueViolation:
                self.send_json(HTTPStatus.CONFLICT, {"error": "That email is already registered."})
                return
            self.log_event("user_registered", user_id=user["id"], email=email, ip=self.client_ip())
            self.create_session(user)
            return

        if path == "/api/login":
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", ""))
            with db_cursor() as cursor:
                cursor.execute("SELECT * FROM user_profiles WHERE email = %s", (email,))
                user = cursor.fetchone()
            if not user or not verify_password(password, user["password_hash"]):
                self.log_event("login_failed", email=email, ip=self.client_ip())
                self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "Invalid email or password."})
                return
            self.log_event("login_success", user_id=user["id"], email=email, ip=self.client_ip())
            self.create_session(user)
            return

        if path == "/api/logout":
            self.send_json(HTTPStatus.OK, {"ok": True}, {"Set-Cookie": clear_cookie_header()})
            return

        if path == "/api/stripe/checkout":
            user = self.require_user()
            if not user:
                return
            try:
                tier = checkout_tier(payload)
                session = create_stripe_checkout_session(user, tier)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            except StripeCheckoutError as exc:
                self.send_json(exc.status, {"error": str(exc)})
                return

            self.log_event("stripe_checkout_created", user_id=user["id"], tier=tier, session_id=session.get("id"), ip=self.client_ip())
            self.send_json(HTTPStatus.CREATED, {"sessionId": session.get("id"), "url": session.get("url")})
            return

        if path == "/api/grants":
            user = self.require_user()
            if not user:
                return
            try:
                values = grant_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO grant_ledger
                        (user_id, grant_name, funding_amount, deadline, application_difficulty, priority_score, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, grant_name, funding_amount, deadline, application_difficulty,
                              priority_score, status, created_at, updated_at
                    """,
                    (
                        user["id"],
                        values["grant_name"],
                        values["funding_amount"],
                        values["deadline"],
                        values["application_difficulty"],
                        values["priority_score"],
                        values["status"],
                    ),
                )
                grant = cursor.fetchone()
            self.log_event("grant_created", user_id=user["id"], grant_id=grant["id"], ip=self.client_ip())
            self.send_json(HTTPStatus.CREATED, {"grant": grant})
            return

        if path == "/api/housing":
            user = self.require_user()
            if not user:
                return
            try:
                values = housing_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO housing_incidents
                        (user_id, category, description, area_location, request_date,
                         resolve_date, severity_level, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING incident_id, category, description, area_location, request_date,
                              resolve_date, severity_level, status, created_at, updated_at
                    """,
                    (
                        user["id"],
                        values["category"],
                        values["description"],
                        values["area_location"],
                        values["request_date"],
                        values["resolve_date"],
                        values["severity_level"],
                        values["status"],
                    ),
                )
                incident = enrich_housing_incident(cursor.fetchone())
            self.log_event("housing_incident_created", user_id=user["id"], incident_id=incident["incident_id"], ip=self.client_ip())
            self.send_json(HTTPStatus.CREATED, {"incident": incident})
            return

        if path == "/api/inventory":
            user = self.require_user()
            if not user:
                return
            try:
                values = inventory_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO asset_inventory
                        (user_id, item_name, category, estimated_market_value, quantity, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING item_id, item_name, category, estimated_market_value, quantity,
                              notes, acquired_at, created_at, updated_at
                    """,
                    (
                        user["id"],
                        values["item_name"],
                        values["category"],
                        values["estimated_market_value"],
                        values["quantity"],
                        values["notes"],
                    ),
                )
                item = enrich_inventory_item(cursor.fetchone())
            self.log_event("inventory_item_created", user_id=user["id"], item_id=item["item_id"], ip=self.client_ip())
            self.send_json(HTTPStatus.CREATED, {"item": item})
            return

        if path == "/api/transactions":
            user = self.require_user()
            if not user:
                return
            try:
                values = transaction_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    INSERT INTO real_estate_listings
                        (tenant_id, agent_id, address_street, address_city, address_state,
                         address_zip, price, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING listing_id
                    """,
                    (
                        user["id"],
                        user["id"],
                        values["address_street"],
                        values["address_city"],
                        values["address_state"],
                        values["address_zip"],
                        values["price"],
                        listing_status_for_stage(values["stage"]),
                    ),
                )
                listing_id = cursor.fetchone()["listing_id"]
                cursor.execute(
                    """
                    INSERT INTO real_estate_transactions
                        (tenant_id, listing_id, agent_id, buyer_name, contract_price,
                         escrow_company, earnest_money_amount, target_closing_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING transaction_id
                    """,
                    (
                        user["id"],
                        listing_id,
                        user["id"],
                        values["buyer_name"],
                        values["price"],
                        values["escrow_company"],
                        values["earnest_money"],
                        values["target_closing_date"],
                        values["stage"],
                    ),
                )
                transaction_id = cursor.fetchone()["transaction_id"]
                if values["milestones"]:
                    execute_values(
                        cursor,
                        """
                        INSERT INTO transaction_milestones
                            (transaction_id, milestone_name, due_date, completed_at, is_critical_drop_dead, notes)
                        VALUES %s
                        """,
                        [(transaction_id, *milestone) for milestone in values["milestones"]],
                    )
            self.log_event("transaction_created", user_id=user["id"], transaction_id=transaction_id, ip=self.client_ip())
            self.send_json(HTTPStatus.CREATED, {"ok": True, "transactionId": transaction_id})
            return

        self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_PUT(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
        grant_id = self.grant_id_from_path(path)
        housing_id = self.housing_id_from_path(path)
        inventory_id = self.inventory_id_from_path(path)
        payload = self.read_json()
        if local_demo_mode() and self.handle_demo_put(path, payload):
            return
        if grant_id is None and housing_id is None and inventory_id is None:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        user = self.require_user()
        if not user:
            return
        if inventory_id is not None:
            try:
                values = inventory_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE asset_inventory
                    SET item_name = %s,
                        category = %s,
                        estimated_market_value = %s,
                        quantity = %s,
                        notes = %s,
                        updated_at = now()
                    WHERE item_id = %s AND user_id = %s
                    RETURNING item_id, item_name, category, estimated_market_value, quantity,
                              notes, acquired_at, created_at, updated_at
                    """,
                    (
                        values["item_name"],
                        values["category"],
                        values["estimated_market_value"],
                        values["quantity"],
                        values["notes"],
                        inventory_id,
                        user["id"],
                    ),
                )
                item = cursor.fetchone()
            if not item:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "Inventory item not found"})
                return
            item = enrich_inventory_item(item)
            self.log_event("inventory_item_updated", user_id=user["id"], item_id=inventory_id, ip=self.client_ip())
            self.send_json(HTTPStatus.OK, {"item": item})
            return

        if housing_id is not None:
            try:
                values = housing_payload(payload)
            except ValueError as exc:
                self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE housing_incidents
                    SET category = %s,
                        description = %s,
                        area_location = %s,
                        request_date = %s,
                        resolve_date = %s,
                        severity_level = %s,
                        status = %s,
                        updated_at = now()
                    WHERE incident_id = %s AND user_id = %s
                    RETURNING incident_id, category, description, area_location, request_date,
                              resolve_date, severity_level, status, created_at, updated_at
                    """,
                    (
                        values["category"],
                        values["description"],
                        values["area_location"],
                        values["request_date"],
                        values["resolve_date"],
                        values["severity_level"],
                        values["status"],
                        housing_id,
                        user["id"],
                    ),
                )
                incident = cursor.fetchone()
            if not incident:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "Housing incident not found"})
                return
            incident = enrich_housing_incident(incident)
            self.log_event("housing_incident_updated", user_id=user["id"], incident_id=housing_id, ip=self.client_ip())
            self.send_json(HTTPStatus.OK, {"incident": incident})
            return

        try:
            values = grant_payload(payload)
        except ValueError as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        with db_cursor(commit=True) as cursor:
            cursor.execute(
                """
                UPDATE grant_ledger
                SET grant_name = %s,
                    funding_amount = %s,
                    deadline = %s,
                    application_difficulty = %s,
                    priority_score = %s,
                    status = %s,
                    updated_at = now()
                WHERE id = %s AND user_id = %s
                RETURNING id, grant_name, funding_amount, deadline, application_difficulty,
                          priority_score, status, created_at, updated_at
                """,
                (
                    values["grant_name"],
                    values["funding_amount"],
                    values["deadline"],
                    values["application_difficulty"],
                    values["priority_score"],
                    values["status"],
                    grant_id,
                    user["id"],
                ),
            )
            grant = cursor.fetchone()

        if not grant:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Grant not found"})
            return
        self.log_event("grant_updated", user_id=user["id"], grant_id=grant_id, ip=self.client_ip())
        self.send_json(HTTPStatus.OK, {"grant": grant})

    def do_PATCH(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
        payload = self.read_json()
        if local_demo_mode() and self.handle_demo_patch(path, payload):
            return

        transaction_id = self.transaction_stage_from_path(path)
        if transaction_id is None:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        user = self.require_user()
        if not user:
            return

        stage = clean_transaction_stage(payload.get("stage", "listing"))
        try:
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    UPDATE real_estate_transactions
                    SET status = %s,
                        updated_at = now()
                    WHERE transaction_id = %s AND tenant_id = %s
                    RETURNING transaction_id, listing_id, status
                    """,
                    (stage, transaction_id, user["id"]),
                )
                updated = cursor.fetchone()
                if not updated:
                    self.send_json(HTTPStatus.NOT_FOUND, {"error": "Transaction not found"})
                    return
                cursor.execute(
                    """
                    UPDATE real_estate_listings
                    SET status = %s,
                        updated_at = now()
                    WHERE listing_id = %s AND tenant_id = %s
                    """,
                    (listing_status_for_stage(stage), updated["listing_id"], user["id"]),
                )
        except Exception as exc:
            self.log_event(
                "transaction_stage_update_failed",
                user_id=user["id"],
                transaction_id=transaction_id,
                stage=stage,
                error_type=type(exc).__name__,
                ip=self.client_ip(),
            )
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Transaction stage update failed"})
            return

        self.log_event("transaction_stage_updated", user_id=user["id"], transaction_id=transaction_id, stage=stage, ip=self.client_ip())
        self.send_json(HTTPStatus.OK, {"ok": True, "transactionId": transaction_id, "stage": stage})

    def do_DELETE(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
        if local_demo_mode() and self.handle_demo_delete(path):
            return

        grant_id = self.grant_id_from_path(path)
        housing_id = self.housing_id_from_path(path)
        inventory_id = self.inventory_id_from_path(path)
        if grant_id is None and housing_id is None and inventory_id is None:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        user = self.require_user()
        if not user:
            return
        if inventory_id is not None:
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    "DELETE FROM asset_inventory WHERE item_id = %s AND user_id = %s RETURNING item_id",
                    (inventory_id, user["id"]),
                )
                deleted = cursor.fetchone()
            if not deleted:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "Inventory item not found"})
                return
            self.log_event("inventory_item_deleted", user_id=user["id"], item_id=inventory_id, ip=self.client_ip())
            self.send_json(HTTPStatus.OK, {"ok": True})
            return

        if housing_id is not None:
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    "DELETE FROM housing_incidents WHERE incident_id = %s AND user_id = %s RETURNING incident_id",
                    (housing_id, user["id"]),
                )
                deleted = cursor.fetchone()
            if not deleted:
                self.send_json(HTTPStatus.NOT_FOUND, {"error": "Housing incident not found"})
                return
            self.log_event("housing_incident_deleted", user_id=user["id"], incident_id=housing_id, ip=self.client_ip())
            self.send_json(HTTPStatus.OK, {"ok": True})
            return

        with db_cursor(commit=True) as cursor:
            cursor.execute(
                "DELETE FROM grant_ledger WHERE id = %s AND user_id = %s RETURNING id",
                (grant_id, user["id"]),
            )
            deleted = cursor.fetchone()
        if not deleted:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Grant not found"})
            return
        self.log_event("grant_deleted", user_id=user["id"], grant_id=grant_id, ip=self.client_ip())
        self.send_json(HTTPStatus.OK, {"ok": True})

    def create_session(self, user: dict) -> None:
        token = create_jwt(user)
        self.send_json(
            HTTPStatus.OK,
            {"user": {"email": user["email"], "displayName": user["display_name"]}},
            {"Set-Cookie": access_cookie_header(token)},
        )


def main() -> None:
    load_dotenv_file()
    config = load_app_settings()
    if config.local_demo_mode and config.app_environment == "production":
        raise RuntimeError("REPO52_DEMO_MODE cannot be enabled when APP_ENV=production.")

    if config.local_demo_mode:
        seed_demo_memory()
        schema_mode = "demo_sqlite"
    else:
        init_pool()
        if config.app_environment == "production" or config.require_alembic_migrations:
            require_alembic_schema()
            schema_mode = "alembic_only"
        else:
            init_db()
            schema_mode = "startup_initializer"

    host = config.dashboard_host
    port = config.dashboard_port
    log_event(
        "api_started",
        host=host,
        port=port,
        database="demo_sqlite" if config.local_demo_mode else "postgresql",
        database_file=str(DEMO_SQLITE_FILE) if config.local_demo_mode else None,
        auth="demo_jwt" if config.local_demo_mode else "jwt",
        schema_mode=schema_mode,
    )
    ThreadingHTTPServer((host, port), ApiHandler).serve_forever()


if __name__ == "__main__":
    main()
