"""Load Repo 52 dashboard ledgers from repo-root data/*.csv (source of truth)."""
from __future__ import annotations

import csv
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from grants import money as grant_money, parse_deadline as grant_parse_deadline, read_grants, score_grant  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
GRANTS_CSV = DATA_DIR / "grants.csv"
HOUSING_CSV = DATA_DIR / "housing_violations.csv"
INVENTORY_CSV = DATA_DIR / "shell_items.csv"

HOUSING_FIELDS = [
    "date",
    "landlord",
    "property",
    "issue",
    "severity",
    "status",
    "penalty",
    "evidence_file",
    "source_url",
    "notes",
]

INVENTORY_FIELDS = [
    "item_name",
    "image_path",
    "condition",
    "rarity_score",
    "comparable_low",
    "comparable_high",
    "source_url",
    "notes",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def csv_data_source_enabled() -> bool:
    import os

    return os.environ.get("REPO52_DATA_SOURCE", "csv").strip().lower() != "seed"


def _file_meta(path: Path) -> dict | None:
    if not path.exists():
        return None
    stat = path.stat()
    return {
        "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "modifiedAt": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sizeBytes": stat.st_size,
    }


def difficulty_for_status(status: str) -> int:
    normalized = (status or "").strip().lower()
    return {
        "ready": 1,
        "eligible": 1,
        "research": 2,
        "applied": 4,
        "submitted": 4,
        "approved": 3,
        "denied": 2,
        "closed": 2,
        "not_fit": 2,
    }.get(normalized, 3)


def load_grant_rows() -> list[dict]:
    rows = read_grants(GRANTS_CSV)
    shaped: list[dict] = []
    for index, row in enumerate(rows, start=1):
        scored = score_grant(row, set())
        deadline = grant_parse_deadline(row.get("deadline", ""))
        funding = grant_money(row.get("amount_max", "")) or grant_money(row.get("amount_min", ""))
        shaped.append(
            {
                "id": index,
                "grant_name": row.get("grant_name", "").strip(),
                "source_url": row.get("source_url", "").strip(),
                "funding_amount": float(funding),
                "deadline": deadline,
                "application_difficulty": difficulty_for_status(row.get("status", "")),
                "status": (row.get("status", "") or "research").strip().lower(),
                "priority_score": round(float(scored.score), 2),
                "eligibility": row.get("eligibility", "").strip(),
                "notes": row.get("notes", "").strip(),
                "action": scored.action,
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
    return shaped


def _read_csv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [{field: (row.get(field) or "").strip() for field in fields} for row in reader]


def _number(value: str) -> float:
    cleaned = (value or "").replace("$", "").replace(",", "").strip()
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_housing_rows() -> list[dict]:
    rows = _read_csv(HOUSING_CSV, HOUSING_FIELDS)
    shaped: list[dict] = []
    for index, row in enumerate(rows, start=1):
        request_date = grant_parse_deadline(row.get("date", "")) or date.today()
        status = (row.get("status") or "open").strip().lower()
        severity = int(_number(row.get("severity", "5")) or 5)
        severity = max(1, min(10, severity))
        notes = row.get("notes", "").strip()
        description = row.get("issue", "").strip()
        if notes and notes not in description:
            description = f"{description} — {notes}" if description else notes
        shaped.append(
            {
                "incident_id": index,
                "category": (row.get("landlord") or "Housing").strip(),
                "description": description,
                "area_location": (row.get("property") or "Unspecified").strip(),
                "source_url": row.get("source_url", "").strip(),
                "request_date": request_date,
                "resolve_date": None,
                "severity_level": severity,
                "status": status,
                "penalty": _number(row.get("penalty", "")),
                "evidence_file": row.get("evidence_file", "").strip(),
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
    return shaped


def estimate_inventory_value(row: dict[str, str]) -> float:
    low = _number(row.get("comparable_low", ""))
    high = _number(row.get("comparable_high", ""))
    rarity = max(0.0, min(_number(row.get("rarity_score", "")), 10.0))
    midpoint = (low + high) / 2 if low and high else max(low, high)
    return max(midpoint * (1 + (rarity - 5) * 0.03), 0.0)


def load_inventory_rows() -> list[dict]:
    rows = _read_csv(INVENTORY_CSV, INVENTORY_FIELDS)
    shaped: list[dict] = []
    for index, row in enumerate(rows, start=1):
        condition = (row.get("condition") or "unknown").strip().title()
        shaped.append(
            {
                "item_id": index,
                "item_name": row.get("item_name", "").strip(),
                "category": condition if condition != "Unknown" else "General",
                "estimated_market_value": round(estimate_inventory_value(row), 2),
                "quantity": 1,
                "source_url": row.get("source_url", "").strip(),
                "notes": row.get("notes", "").strip(),
                "acquired_at": utc_now(),
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
    return shaped


def build_data_meta(*, loaded: bool, error: str | None = None) -> dict:
    files = {
        "grants": _file_meta(GRANTS_CSV),
        "housing": _file_meta(HOUSING_CSV),
        "inventory": _file_meta(INVENTORY_CSV),
    }
    return {
        "source": "csv" if loaded else "seed",
        "loadedAt": utc_now().isoformat(),
        "dataDirectory": str(DATA_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
        "files": files,
        "error": error,
    }


def load_repo_csv_ledgers() -> tuple[dict[str, list[dict]], dict]:
    """Return ({grants, housing, inventory}, meta). Raises if CSV source enabled but files missing."""
    if not csv_data_source_enabled():
        return {}, build_data_meta(loaded=False)

    missing = [path.name for path in (GRANTS_CSV, HOUSING_CSV, INVENTORY_CSV) if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing CSV data files in {DATA_DIR}: {', '.join(missing)}")

    grants = load_grant_rows()
    housing = load_housing_rows()
    inventory = load_inventory_rows()
    meta = build_data_meta(loaded=True)
    meta["counts"] = {
        "grants": len(grants),
        "housing": len(housing),
        "inventory": len(inventory),
    }
    return {"grants": grants, "housing": housing, "inventory": inventory}, meta