from __future__ import annotations

import csv
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
DB_PATH = ROOT / "dashboard.db"
SEED_CSV = REPO_ROOT / "output" / "paper_portfolio_plan.csv"
DEFAULT_ASSETS = [
    ("BTC", "Bitcoin", 0.2424, 242.36, 0.24, 0.46),
    ("ETH", "Ethereum", 0.2389, 238.88, 0.18, 0.42),
    ("SOL", "Solana", 0.2394, 239.42, 0.35, 0.62),
    ("NVDA", "NVIDIA Corp", 0.2793, 279.34, 0.28, 0.38),
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS portfolio_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                name TEXT NOT NULL,
                target_weight REAL NOT NULL,
                paper_cash REAL NOT NULL,
                expected_return REAL NOT NULL,
                volatility REAL NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
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


def seed_user_assets(db: sqlite3.Connection, user_id: int) -> None:
    now = utc_now().isoformat()
    db.executemany(
        """
        INSERT INTO portfolio_assets
            (user_id, ticker, name, target_weight, paper_cash, expected_return, volatility, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(user_id, *asset, now) for asset in load_seed_assets()],
    )


class ApiHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def send_json(self, status: int, payload: dict, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("SameSite", "Lax")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

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
            if key == "session_id" and value:
                return value
        return None

    def current_user(self) -> sqlite3.Row | None:
        token = self.cookie_token()
        if not token:
            return None
        with connect() as db:
            row = db.execute(
                """
                SELECT users.* FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token = ? AND sessions.expires_at > ?
                """,
                (token, utc_now().isoformat()),
            ).fetchone()
            return row

    def require_user(self) -> sqlite3.Row | None:
        user = self.current_user()
        if user is None:
            self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "Authentication required"})
        return user

    def do_GET(self) -> None:
        path = urlparse(self.path).path
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
            with connect() as db:
                assets = db.execute(
                    """
                    SELECT ticker, name, target_weight, paper_cash, expected_return, volatility, updated_at
                    FROM portfolio_assets
                    WHERE user_id = ?
                    ORDER BY target_weight DESC
                    """,
                    (user["id"],),
                ).fetchall()
            total_cash = sum(float(asset["paper_cash"]) for asset in assets)
            weighted_return = sum(float(asset["target_weight"]) * float(asset["expected_return"]) for asset in assets)
            weighted_risk = sum((float(asset["target_weight"]) * float(asset["volatility"])) ** 2 for asset in assets) ** 0.5
            self.send_json(
                HTTPStatus.OK,
                {
                    "summary": {
                        "totalCash": round(total_cash, 2),
                        "weightedReturn": round(weighted_return, 4),
                        "weightedRisk": round(weighted_risk, 4),
                        "assetCount": len(assets),
                    },
                    "assets": [dict(asset) for asset in assets],
                },
            )
            return

        self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
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
                with connect() as db:
                    cursor = db.execute(
                        "INSERT INTO users (email, display_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
                        (email, display_name, hash_password(password), utc_now().isoformat()),
                    )
                    seed_user_assets(db, int(cursor.lastrowid))
            except sqlite3.IntegrityError:
                self.send_json(HTTPStatus.CONFLICT, {"error": "That email is already registered."})
                return
            self.create_session(email)
            return

        if path == "/api/login":
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", ""))
            with connect() as db:
                user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if not user or not verify_password(password, user["password_hash"]):
                self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "Invalid email or password."})
                return
            self.create_session(email)
            return

        if path == "/api/logout":
            token = self.cookie_token()
            if token:
                with connect() as db:
                    db.execute("DELETE FROM sessions WHERE token = ?", (token,))
            self.send_json(HTTPStatus.OK, {"ok": True}, {"Set-Cookie": "session_id=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"})
            return

        self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def create_session(self, email: str) -> None:
        token = secrets.token_urlsafe(32)
        expires_at = (utc_now() + timedelta(days=14)).isoformat()
        with connect() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            db.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user["id"], expires_at))
        self.send_json(
            HTTPStatus.OK,
            {"user": {"email": user["email"], "displayName": user["display_name"]}},
            {"Set-Cookie": f"session_id={token}; Path=/; Max-Age=1209600; HttpOnly; SameSite=Lax"},
        )


def main() -> None:
    init_db()
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "8787"))
    print(f"Dashboard API listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), ApiHandler).serve_forever()


if __name__ == "__main__":
    main()
