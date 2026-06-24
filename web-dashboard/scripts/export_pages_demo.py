"""Export read-only demo JSON for GitHub Pages static hosting."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server import (  # noqa: E402
    DEMO_USER,
    demo_grants_payload,
    demo_housing_payload,
    demo_inventory_payload,
    demo_optimizer_jobs_payload,
    demo_optimizer_runs_payload,
    demo_portfolio_payload,
    demo_transactions_payload,
    optimizer_payload,
    seed_demo_memory,
)

OUT = ROOT / "public" / "demo"


def write(name: str, payload: dict) -> None:
    path = OUT / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def main() -> None:
    seed_demo_memory()
    OUT.mkdir(parents=True, exist_ok=True)
    write("me.json", {"user": {"email": DEMO_USER["email"], "displayName": DEMO_USER["display_name"]}})
    write("grants.json", demo_grants_payload())
    write("housing.json", demo_housing_payload())
    write("inventory.json", demo_inventory_payload())
    write("portfolio.json", demo_portfolio_payload())
    write("transactions.json", demo_transactions_payload())
    write("optimizer-runs.json", demo_optimizer_runs_payload())
    write("optimizer-jobs.json", demo_optimizer_jobs_payload())
    write("optimizer-classical.json", optimizer_payload("classical"))
    write("optimizer-quantum.json", optimizer_payload("quantum"))


if __name__ == "__main__":
    main()