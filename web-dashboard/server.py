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
RATE_LIMIT_LOCK = threading.Lock()
RATE_LIMIT_BUCKETS: dict[str, list[float]] = {}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def log_event(event: str, **fields) -> None:
    payload = {
        "ts": utc_now().isoformat(),
        "event": event,
        **fields,
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


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required.")
    return value


def database_url() -> str:
    return required_env("DATABASE_URL")


def jwt_secret() -> str:
    value = required_env("JWT_SECRET")
    if len(value) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters.")
    return value


def allowed_origins() -> set[str]:
    configured = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8080,http://localhost:8080",
    )
    return {origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()}


def cookie_secure() -> bool:
    return os.environ.get("COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes"}


def access_token_max_age() -> int:
    return int(os.environ.get("JWT_TTL_SECONDS", "1209600"))


def init_pool() -> None:
    global POOL
    if POOL is not None:
        return
    POOL = ThreadedConnectionPool(
        minconn=int(os.environ.get("DATABASE_POOL_MIN", "1")),
        maxconn=int(os.environ.get("DATABASE_POOL_MAX", "10")),
        dsn=database_url(),
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
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
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
        limit = int(os.environ.get("RATE_LIMIT_AUTH_PER_MINUTE" if is_auth else "RATE_LIMIT_API_PER_MINUTE", "12" if is_auth else "120"))
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

        self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_PUT(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
        grant_id = self.grant_id_from_path(path)
        if grant_id is None:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        user = self.require_user()
        if not user:
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

    def do_DELETE(self) -> None:
        if not self.rate_limit():
            self.send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"})
            return

        path = urlparse(self.path).path
        grant_id = self.grant_id_from_path(path)
        if grant_id is None:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        user = self.require_user()
        if not user:
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
    jwt_secret()
    init_pool()
    init_db()
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "8787"))
    log_event("api_started", host=host, port=port, database="postgresql", auth="jwt")
    ThreadingHTTPServer((host, port), ApiHandler).serve_forever()


if __name__ == "__main__":
    main()
