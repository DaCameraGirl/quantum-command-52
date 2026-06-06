from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "shell_items.csv"
OUTPUT_DIR = ROOT / "output"
OUTPUT_CSV = OUTPUT_DIR / "shell_catalog_estimates.csv"

FIELDS = [
    "item_name",
    "image_path",
    "condition",
    "rarity_score",
    "comparable_low",
    "comparable_high",
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


def estimate_row(row: dict[str, str]) -> dict[str, str]:
    low = number(row.get("comparable_low", ""))
    high = number(row.get("comparable_high", ""))
    rarity = max(0.0, min(number(row.get("rarity_score", "")), 10.0))
    midpoint = (low + high) / 2 if low and high else max(low, high)
    rarity_adjustment = 1 + (rarity - 5) * 0.03
    estimated = max(midpoint * rarity_adjustment, 0)
    return {
        **row,
        "estimated_value": f"{estimated:.2f}",
        "confidence": "medium" if low and high else "low",
        "next_action": "Get professional appraisal for insurance or high-value sale."
        if estimated >= 500
        else "Keep cataloged; compare with more completed sales before pricing.",
    }


def estimate() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing {DATA_FILE}.")
    with DATA_FILE.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = [{field: row.get(field, "") for field in FIELDS} for row in csv.DictReader(handle)]

    results = [estimate_row(row) for row in rows]
    results.sort(key=lambda row: number(row["estimated_value"]), reverse=True)

    OUTPUT_DIR.mkdir(exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*FIELDS, "estimated_value", "confidence", "next_action"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {OUTPUT_CSV}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate catalog values from comparable sale ranges.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("estimate", help="Write shell catalog estimate CSV.")
    args = parser.parse_args()
    if args.command in {None, "estimate"}:
        estimate()


if __name__ == "__main__":
    main()
