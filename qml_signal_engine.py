from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FEATURE_FILE = ROOT / "data" / "market_features.csv"
ASSET_FILE = ROOT / "data" / "portfolio_assets.csv"
OUTPUT_DIR = ROOT / "output"
OUTPUT_CSV = OUTPUT_DIR / "qml_paper_signal_manifest.csv"
OUTPUT_MD = OUTPUT_DIR / "qml_paper_signal_summary.md"


FEATURE_COLUMNS = [
    "ticker",
    "momentum_30d",
    "momentum_90d",
    "rsi",
    "volume_spike",
    "volatility",
    "sentiment",
    "liquidity",
]


@dataclass(frozen=True)
class SignalInput:
    ticker: str
    features: list[float]
    price: float


def number(value: str, default: float = 0.0) -> float:
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    if not cleaned:
        return default
    try:
        return float(cleaned)
    except ValueError:
        return default


def load_prices() -> dict[str, float]:
    if not ASSET_FILE.exists():
        return {}
    with ASSET_FILE.open("r", newline="", encoding="utf-8-sig") as handle:
        return {
            row.get("ticker", "").strip().upper(): number(row.get("current_price", ""))
            for row in csv.DictReader(handle)
        }


def load_features() -> list[SignalInput]:
    if not FEATURE_FILE.exists():
        raise FileNotFoundError(f"Missing {FEATURE_FILE}")

    prices = load_prices()
    inputs: list[SignalInput] = []
    with FEATURE_FILE.open("r", newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            ticker = row.get("ticker", "").strip().upper()
            if not ticker:
                continue
            features = [number(row.get(column, "")) for column in FEATURE_COLUMNS[1:]]
            inputs.append(SignalInput(ticker=ticker, features=features, price=prices.get(ticker, 0.0)))
    if not inputs:
        raise ValueError("No feature rows found.")
    return inputs


def normalize_feature(value: float, column_index: int) -> float:
    # Maps mixed financial indicator ranges into stable angle inputs.
    if column_index == 2:  # RSI, usually 0..100
        scaled = (value - 50.0) / 50.0
    else:
        scaled = value
    return max(-1.0, min(1.0, scaled))


def classical_compressor(features: list[float]) -> list[float]:
    """
    Deterministic stand-in for a small classical neural feature compressor.

    This is intentionally transparent: it lets the repo run without PyTorch, then
    the same input/output shape can be replaced by torch.nn later.
    """
    normalized = [normalize_feature(value, index) for index, value in enumerate(features)]
    return [
        0.50 * normalized[0] + 0.30 * normalized[1] + 0.20 * normalized[5],
        -0.45 * normalized[2] + 0.25 * normalized[3] - 0.30 * normalized[4],
        0.35 * normalized[0] - 0.20 * normalized[4] + 0.25 * normalized[6],
        0.30 * normalized[1] + 0.25 * normalized[3] + 0.15 * normalized[5],
    ]


def quantum_hidden_layer(compressed: list[float], depth: int) -> float:
    """
    QML-shaped parametric hidden layer.

    It converts compressed classical features into rotation-like angles, then
    mixes them through nonlinear trigonometric terms. This is not IBM hardware;
    it is the local structural prototype for one future Qiskit layer.
    """
    state = compressed[:]
    for layer in range(depth):
        mixed = []
        for index, value in enumerate(state):
            neighbor = state[(index + 1) % len(state)]
            angle = math.pi * (value + 0.15 * neighbor + 0.05 * layer)
            mixed.append(math.sin(angle) ** 2 - 0.5 * math.cos(angle / 2))
        state = mixed
    return sum(state) / len(state)


def softmax(values: list[float]) -> list[float]:
    peak = max(values)
    exps = [math.exp(value - peak) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def generate_manifest(inputs: list[SignalInput], capital: float, depth: int) -> list[dict[str, str]]:
    raw_scores = []
    compressed_by_ticker = {}
    for item in inputs:
        compressed = classical_compressor(item.features)
        compressed_by_ticker[item.ticker] = compressed
        raw_scores.append(quantum_hidden_layer(compressed, depth=depth))

    allocations = softmax(raw_scores)
    rows = []
    for item, score, weight in zip(inputs, raw_scores, allocations):
        cash = capital * weight
        units = cash / item.price if item.price > 0 else 0.0
        rows.append(
            {
                "ticker": item.ticker,
                "qml_signal_score": f"{score:.6f}",
                "target_weight": f"{weight:.4f}",
                "target_percent": f"{weight * 100:.2f}%",
                "paper_cash": f"{cash:.2f}",
                "price": f"{item.price:.2f}",
                "paper_units": f"{units:.8f}",
                "compressed_features": ";".join(f"{value:.4f}" for value in compressed_by_ticker[item.ticker]),
            }
        )
    rows.sort(key=lambda row: number(row["target_weight"]), reverse=True)
    return rows


def write_outputs(rows: list[dict[str, str]], capital: float, depth: int) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# QML Paper Signal Summary",
        "",
        "This is a local QML-shaped prototype, not financial advice and not a trading bot.",
        "",
        f"- Paper capital: ${capital:,.2f}",
        f"- Quantum hidden depth: {depth}",
        f"- Assets scored: {len(rows)}",
        "",
        "## Allocation",
    ]
    for row in rows:
        lines.append(
            f"- {row['ticker']}: {row['target_percent']} | signal {row['qml_signal_score']} | ${row['paper_cash']}"
        )
    lines.extend(
        [
            "",
            "## Why This Exists",
            "",
            "The previous QML examples used random tensors and cloud-only dependencies.",
            "This version reads real feature rows from CSV and creates reproducible paper output.",
            "A future PyTorch/Qiskit version should add real training labels, backtesting, and validation before any live use.",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Local QML-shaped paper signal engine.")
    parser.add_argument("--capital", type=float, default=1000.0)
    parser.add_argument("--depth", type=int, default=3)
    args = parser.parse_args()

    rows = generate_manifest(load_features(), capital=args.capital, depth=args.depth)
    write_outputs(rows, capital=args.capital, depth=args.depth)
    print(f"Wrote {OUTPUT_CSV}")
    print(f"Wrote {OUTPUT_MD}")


if __name__ == "__main__":
    main()

