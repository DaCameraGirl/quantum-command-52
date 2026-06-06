from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "housing_violations.csv"
OUTPUT_DIR = ROOT / "output"
OUTPUT_CSV = OUTPUT_DIR / "urgent_housing_violations.csv"
OUTPUT_MD = OUTPUT_DIR / "housing_evidence_summary.md"

FIELDS = [
    "date",
    "landlord",
    "property",
    "issue",
    "severity",
    "status",
    "penalty",
    "evidence_file",
    "notes",
]


def number(value: str) -> float:
    cleaned = value.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}.")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [{field: row.get(field, "") for field in FIELDS} for row in reader]


def summarize(min_severity: float) -> None:
    rows = load_rows(DATA_FILE)
    urgent = [
        row
        for row in rows
        if row.get("status", "").strip().lower() not in {"resolved", "closed"}
        and number(row.get("severity", "")) >= min_severity
    ]
    urgent.sort(key=lambda row: number(row.get("severity", "")), reverse=True)

    OUTPUT_DIR.mkdir(exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(urgent)

    total_penalty = sum(number(row.get("penalty", "")) for row in urgent)
    landlords = Counter(row.get("landlord", "").strip() or "unknown" for row in urgent)

    lines = [
        "# Housing Evidence Summary",
        "",
        "This is an organizer, not legal advice.",
        "",
        f"- Urgent unresolved issues: {len(urgent)}",
        f"- Total listed penalties/damages: ${total_penalty:,.2f}",
        f"- Minimum severity used: {min_severity:g}",
        "",
        "## Landlords / Parties",
    ]
    for landlord, count in landlords.most_common():
        lines.append(f"- {landlord}: {count} issue(s)")

    lines.extend(["", "## Urgent Issues"])
    for row in urgent:
        lines.extend(
            [
                f"### {row.get('date', 'unknown date')} - {row.get('issue', 'unknown issue')}",
                f"- Property: {row.get('property', '').strip() or 'unknown'}",
                f"- Landlord: {row.get('landlord', '').strip() or 'unknown'}",
                f"- Severity: {row.get('severity', '').strip() or 'unknown'}",
                f"- Evidence: {row.get('evidence_file', '').strip() or 'not attached'}",
                f"- Notes: {row.get('notes', '').strip() or 'none'}",
                "",
            ]
        )

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT_CSV}")
    print(f"Wrote {OUTPUT_MD}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize unresolved housing violations.")
    subparsers = parser.add_subparsers(dest="command")
    summarize_parser = subparsers.add_parser("summarize", help="Write urgent issue summary files.")
    summarize_parser.add_argument("--min-severity", type=float, default=8.0)
    args = parser.parse_args()
    if args.command in {None, "summarize"}:
        summarize(getattr(args, "min_severity", 8.0))


if __name__ == "__main__":
    main()
