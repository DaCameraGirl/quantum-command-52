from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "grants.csv"
OUTPUT_DIR = ROOT / "output"
OUTPUT_CSV = OUTPUT_DIR / "ranked_grants.csv"
OUTPUT_MD = OUTPUT_DIR / "grant_action_list.md"


FIELDS = [
    "grant_name",
    "source_url",
    "amount_min",
    "amount_max",
    "deadline",
    "eligibility",
    "women_focused",
    "emergency_funding",
    "no_cosigner",
    "status",
    "notes",
]


@dataclass
class Grant:
    row: dict[str, str]
    score: float
    action: str


def yes(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def money(value: str) -> float:
    cleaned = value.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_deadline(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def score_grant(row: dict[str, str], profile_terms: set[str]) -> Grant:
    score = 0.0
    status = row.get("status", "").strip().lower()
    amount_max = money(row.get("amount_max", ""))
    deadline = parse_deadline(row.get("deadline", ""))

    score += min(amount_max / 1000.0, 50.0)

    if yes(row.get("women_focused", "")):
        score += 15
    if yes(row.get("emergency_funding", "")):
        score += 15
    if yes(row.get("no_cosigner", "")):
        score += 10

    if deadline:
        days_left = (deadline - date.today()).days
        if days_left < 0:
            score -= 1000
        elif days_left <= 7:
            score += 20
        elif days_left <= 30:
            score += 15
        elif days_left <= 60:
            score += 8
    else:
        score -= 5

    haystack = " ".join(
        [
            row.get("grant_name", ""),
            row.get("eligibility", ""),
            row.get("notes", ""),
        ]
    ).lower()
    matches = sum(1 for term in profile_terms if term and term in haystack)
    score += min(matches * 3, 18)

    if status in {"not_fit", "rejected", "closed"}:
        score -= 500
    elif status in {"applied", "submitted"}:
        score -= 25
    elif status in {"eligible", "ready"}:
        score += 12

    action = next_action(row, deadline)
    return Grant(row=row, score=score, action=action)


def next_action(row: dict[str, str], deadline: date | None) -> str:
    status = row.get("status", "").strip().lower()
    if status in {"applied", "submitted"}:
        return "Track follow-up date and confirmation number."
    if status in {"not_fit", "rejected", "closed"}:
        return "Ignore unless eligibility changes."
    if deadline and deadline < date.today():
        return "Deadline passed; verify whether a new cycle opened."
    if not row.get("source_url", "").strip():
        return "Find the official application URL before doing anything else."
    return "Check eligibility, gather documents, and apply from the official source."


def read_grants(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run: python grants.py init")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [{field: row.get(field, "") for field in FIELDS} for row in reader]


def write_outputs(grants: list[Grant]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["score", "action", *FIELDS])
        writer.writeheader()
        for grant in grants:
            writer.writerow(
                {
                    "score": f"{grant.score:.1f}",
                    "action": grant.action,
                    **grant.row,
                }
            )

    lines = ["# Grant Action List", ""]
    for index, grant in enumerate(grants[:20], start=1):
        row = grant.row
        amount = row.get("amount_max", "").strip() or "unknown amount"
        lines.extend(
            [
                f"## {index}. {row.get('grant_name', 'Unnamed grant')}",
                f"- Score: {grant.score:.1f}",
                f"- Amount max: {amount}",
                f"- Deadline: {row.get('deadline', '').strip() or 'unknown'}",
                f"- Source: {row.get('source_url', '').strip() or 'needs official URL'}",
                f"- Action: {grant.action}",
                f"- Notes: {row.get('notes', '').strip() or 'none'}",
                "",
            ]
        )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def init_file() -> None:
    DATA_FILE.parent.mkdir(exist_ok=True)
    if DATA_FILE.exists():
        print(f"{DATA_FILE} already exists; leaving it alone.")
        return
    with DATA_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "grant_name": "Sample Emergency Aid Fund",
                "source_url": "https://example.org/official-application",
                "amount_min": "500",
                "amount_max": "2500",
                "deadline": "2026-07-15",
                "eligibility": "Adults with urgent housing, school, or safety expenses",
                "women_focused": "yes",
                "emergency_funding": "yes",
                "no_cosigner": "yes",
                "status": "research",
                "notes": "Replace this sample with a real official source.",
            }
        )
    print(f"Created {DATA_FILE}")


def rank(profile: str) -> None:
    profile_terms = {term.strip().lower() for term in profile.split(",") if term.strip()}
    ranked = [score_grant(row, profile_terms) for row in read_grants(DATA_FILE)]
    ranked.sort(key=lambda grant: grant.score, reverse=True)
    write_outputs(ranked)
    print(f"Wrote {OUTPUT_CSV}")
    print(f"Wrote {OUTPUT_MD}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank real grant opportunities from a CSV.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Create data/grants.csv if it does not exist.")
    rank_parser = subparsers.add_parser("rank", help="Rank grants and write output files.")
    rank_parser.add_argument(
        "--profile",
        default="women,emergency,housing,education,school,training,low income",
        help="Comma-separated terms that should score higher when found.",
    )
    args = parser.parse_args()

    if args.command == "init":
        init_file()
    elif args.command == "rank":
        rank(args.profile)


if __name__ == "__main__":
    main()

