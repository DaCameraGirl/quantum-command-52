from __future__ import annotations

import csv
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

import jwt
from app_config import AppSettings, load_settings_from_env
from psycopg2 import errors
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.pool import ThreadedConnectionPool


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
ENV_FILE = REPO_ROOT / ".env"
SEED_CSV = REPO_ROOT / "output" / "paper_portfolio_plan.csv"
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
            """
        )


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
        merged_headers = {**self.cors_headers(), **(headers or {})}
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in merged_headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)
        log_event(
            "api_response",
            method=self.command,
            path=urlparse(self.path).path,
            status=int(status),
            ip=self.client_ip(),
        )

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin", "").rstrip("/")
        if origin and origin not in allowed_origins():
            self.send_json(HTTPStatus.FORBIDDEN, {"error": "Origin not allowed"})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        for key, value in self.cors_headers().items():
            self.send_header(key, value)
        self.end_headers()

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
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
                log_event("rate_limit_block", path=path, ip=self.client_ip(), limit=limit)
                return False
            bucket.append(now)
            RATE_LIMIT_BUCKETS[key] = bucket
        return True

    def current_user(self) -> dict | None:
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

    def do_GET(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json(HTTPStatus.OK, {"ok": True, "database": "postgresql", "auth": "jwt"})
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

            log_event("portfolio_payload", user_id=user["id"], asset_count=len(assets), ip=self.client_ip())
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
            log_event("grant_ledger_list", user_id=user["id"], count=len(grants), ip=self.client_ip())
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
            log_event("housing_incident_list", user_id=user["id"], count=len(incidents), ip=self.client_ip())
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
            log_event("inventory_list", user_id=user["id"], count=len(items), ip=self.client_ip())
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
            log_event("transaction_pipeline_list", user_id=user["id"], count=len(deals), ip=self.client_ip())
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

        self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
        payload = self.read_json()

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
            log_event("user_registered", user_id=user["id"], email=email, ip=self.client_ip())
            self.create_session(user)
            return

        if path == "/api/login":
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", ""))
            with db_cursor() as cursor:
                cursor.execute("SELECT * FROM user_profiles WHERE email = %s", (email,))
                user = cursor.fetchone()
            if not user or not verify_password(password, user["password_hash"]):
                log_event("login_failed", email=email, ip=self.client_ip())
                self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "Invalid email or password."})
                return
            log_event("login_success", user_id=user["id"], email=email, ip=self.client_ip())
            self.create_session(user)
            return

        if path == "/api/logout":
            self.send_json(HTTPStatus.OK, {"ok": True}, {"Set-Cookie": clear_cookie_header()})
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
            log_event("grant_created", user_id=user["id"], grant_id=grant["id"], ip=self.client_ip())
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
            log_event("housing_incident_created", user_id=user["id"], incident_id=incident["incident_id"], ip=self.client_ip())
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
            log_event("inventory_item_created", user_id=user["id"], item_id=item["item_id"], ip=self.client_ip())
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
            log_event("transaction_created", user_id=user["id"], transaction_id=transaction_id, ip=self.client_ip())
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
        if grant_id is None and housing_id is None and inventory_id is None:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        user = self.require_user()
        if not user:
            return
        if inventory_id is not None:
            try:
                values = inventory_payload(self.read_json())
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
            log_event("inventory_item_updated", user_id=user["id"], item_id=inventory_id, ip=self.client_ip())
            self.send_json(HTTPStatus.OK, {"item": item})
            return

        if housing_id is not None:
            try:
                values = housing_payload(self.read_json())
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
            log_event("housing_incident_updated", user_id=user["id"], incident_id=housing_id, ip=self.client_ip())
            self.send_json(HTTPStatus.OK, {"incident": incident})
            return

        try:
            values = grant_payload(self.read_json())
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
        log_event("grant_updated", user_id=user["id"], grant_id=grant_id, ip=self.client_ip())
        self.send_json(HTTPStatus.OK, {"grant": grant})

    def do_PATCH(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
        transaction_id = self.transaction_stage_from_path(path)
        if transaction_id is None:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        user = self.require_user()
        if not user:
            return

        payload = self.read_json()
        stage = clean_transaction_stage(payload.get("stage", "listing"))
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

        log_event("transaction_stage_updated", user_id=user["id"], transaction_id=transaction_id, stage=stage, ip=self.client_ip())
        self.send_json(HTTPStatus.OK, {"ok": True, "transactionId": transaction_id, "stage": stage})

    def do_DELETE(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
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
            log_event("inventory_item_deleted", user_id=user["id"], item_id=inventory_id, ip=self.client_ip())
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
            log_event("housing_incident_deleted", user_id=user["id"], incident_id=housing_id, ip=self.client_ip())
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
        log_event("grant_deleted", user_id=user["id"], grant_id=grant_id, ip=self.client_ip())
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
    init_pool()
    init_db()
    host = config.dashboard_host
    port = config.dashboard_port
    log_event("api_started", host=host, port=port, database="postgresql", auth="jwt")
    ThreadingHTTPServer((host, port), ApiHandler).serve_forever()


if __name__ == "__main__":
    main()
