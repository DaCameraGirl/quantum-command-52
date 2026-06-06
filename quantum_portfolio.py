from __future__ import annotations

import argparse
import asyncio
import csv
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path


try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
except ImportError:  # rich is optional; the engine still works without it.
    Console = None
    Live = None
    Panel = None
    Table = None


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "portfolio_assets.csv"
OUTPUT_DIR = ROOT / "output"
OUTPUT_CSV = OUTPUT_DIR / "paper_portfolio_plan.csv"
OUTPUT_MD = OUTPUT_DIR / "paper_portfolio_summary.md"


FIELDS = [
    "ticker",
    "name",
    "current_price",
    "expected_return",
    "volatility",
    "risk_limit",
    "notes",
]


@dataclass(frozen=True)
class Asset:
    ticker: str
    name: str
    current_price: float
    expected_return: float
    volatility: float
    risk_limit: float
    notes: str


@dataclass(frozen=True)
class PortfolioResult:
    cycle: int
    parameters: list[float]
    weights: list[float]
    expected_return: float
    risk: float
    sharpe: float
    score: float


class OptionalDashboard:
    def __init__(self, enabled: bool):
        self.enabled = enabled and Console is not None and Table is not None and Live is not None and Panel is not None
        self.console = Console() if Console is not None else None
        self.table = None
        self.live = None

    def __enter__(self) -> "OptionalDashboard":
        if self.enabled:
            self.table = Table(title="Quantum Portfolio Telemetry")
            self.table.add_column("Cycle", justify="right")
            self.table.add_column("Allocation")
            self.table.add_column("Risk", justify="right")
            self.table.add_column("Sharpe", justify="right")
            self.table.add_column("Score", justify="right")
            self.live = Live(Panel(self.table, title="Local Quantum Feed", border_style="cyan"), refresh_per_second=6)
            self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.live:
            self.live.__exit__(exc_type, exc, tb)

    def log(self, result: PortfolioResult, assets: list[Asset]) -> None:
        allocation = " | ".join(
            f"{asset.ticker}: {weight * 100:.1f}%" for asset, weight in zip(assets, result.weights)
        )
        if self.enabled and self.table is not None and self.live is not None and Panel is not None:
            self.table.add_row(
                f"{result.cycle}",
                allocation,
                f"{result.risk * 100:.2f}%",
                f"{result.sharpe:.4f}",
                f"{result.score:.4f}",
            )
            self.live.update(Panel(self.table, title="Local Quantum Feed", border_style="cyan"))
        else:
            print(
                f"cycle={result.cycle:03d} risk={result.risk:.4f} "
                f"sharpe={result.sharpe:.4f} score={result.score:.4f} {allocation}"
            )


def number(value: str, default: float = 0.0) -> float:
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    if not cleaned:
        return default
    try:
        return float(cleaned)
    except ValueError:
        return default


def read_assets(path: Path) -> list[Asset]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        assets = []
        for row in rows:
            ticker = row.get("ticker", "").strip().upper()
            if not ticker:
                continue
            assets.append(
                Asset(
                    ticker=ticker,
                    name=row.get("name", "").strip() or ticker,
                    current_price=number(row.get("current_price", "")),
                    expected_return=number(row.get("expected_return", "")),
                    volatility=number(row.get("volatility", "")),
                    risk_limit=number(row.get("risk_limit", ""), 1.0),
                    notes=row.get("notes", "").strip(),
                )
            )
    if not 2 <= len(assets) <= 6:
        raise ValueError("Use 2 to 6 assets in data/portfolio_assets.csv for this local simulator.")
    return assets


def apply_single_qubit_gate(
    state: list[complex],
    qubit: int,
    matrix: tuple[tuple[complex, complex], tuple[complex, complex]],
) -> list[complex]:
    result = state[:]
    bit = 1 << qubit
    for index in range(len(state)):
        if index & bit:
            continue
        paired = index | bit
        a0 = state[index]
        a1 = state[paired]
        result[index] = matrix[0][0] * a0 + matrix[0][1] * a1
        result[paired] = matrix[1][0] * a0 + matrix[1][1] * a1
    return result


def apply_cnot(state: list[complex], control: int, target: int) -> list[complex]:
    result = state[:]
    control_bit = 1 << control
    target_bit = 1 << target
    for index, amplitude in enumerate(state):
        if index & control_bit:
            swapped = index ^ target_bit
            result[swapped] = amplitude
        else:
            result[index] = amplitude
    return result


def build_qnn_probabilities(parameters: list[float], asset_count: int) -> list[float]:
    """
    Local statevector simulation of a small QNN-shaped ansatz:
    H layer -> RY parameter layer -> cyclic entanglement -> RZ phase layer.
    """
    qubits = asset_count
    size = 1 << qubits
    state = [0j] * size
    state[0] = 1 + 0j

    inv_sqrt_2 = 1 / math.sqrt(2)
    h_gate = ((inv_sqrt_2, inv_sqrt_2), (inv_sqrt_2, -inv_sqrt_2))
    for qubit in range(qubits):
        state = apply_single_qubit_gate(state, qubit, h_gate)

    for qubit in range(qubits):
        theta = parameters[qubit]
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        ry_gate = ((c, -s), (s, c))
        state = apply_single_qubit_gate(state, qubit, ry_gate)

    for qubit in range(qubits - 1):
        state = apply_cnot(state, qubit, qubit + 1)
    state = apply_cnot(state, qubits - 1, 0)

    for qubit in range(qubits):
        phi = parameters[qubits + qubit]
        rz_gate = (
            (complex(math.cos(-phi / 2), math.sin(-phi / 2)), 0j),
            (0j, complex(math.cos(phi / 2), math.sin(phi / 2))),
        )
        state = apply_single_qubit_gate(state, qubit, rz_gate)

    return [abs(amplitude) ** 2 for amplitude in state]


def probabilities_to_weights(probabilities: list[float], asset_count: int) -> list[float]:
    raw = [0.0] * asset_count
    for basis_index, probability in enumerate(probabilities):
        for asset_index in range(asset_count):
            if basis_index & (1 << asset_index):
                raw[asset_index] += probability

    total = sum(raw)
    if total <= 0:
        return [1 / asset_count] * asset_count
    return [value / total for value in raw]


def evaluate(
    assets: list[Asset],
    parameters: list[float],
    risk_aversion: float,
    cycle: int,
) -> PortfolioResult:
    probabilities = build_qnn_probabilities(parameters, len(assets))
    weights = probabilities_to_weights(probabilities, len(assets))
    expected_return = sum(weight * asset.expected_return for weight, asset in zip(weights, assets))

    # Conservative diagonal risk model. Later this can be upgraded to a full covariance CSV.
    variance = sum((weight * asset.volatility) ** 2 for weight, asset in zip(weights, assets))
    risk = math.sqrt(max(variance, 0.0))
    sharpe = expected_return / (risk + 1e-9)
    limit_penalty = sum(
        max(0.0, weight - asset.risk_limit) * 5.0 for weight, asset in zip(weights, assets)
    )
    concentration_penalty = max(0.0, max(weights) - 0.80) * 2.0
    score = expected_return - risk_aversion * risk - limit_penalty - concentration_penalty
    return PortfolioResult(
        cycle=cycle,
        parameters=parameters,
        weights=weights,
        expected_return=expected_return,
        risk=risk,
        sharpe=sharpe,
        score=score,
    )


async def evaluate_candidate(
    assets: list[Asset],
    parameters: list[float],
    risk_aversion: float,
    cycle: int,
) -> PortfolioResult:
    await asyncio.sleep(0)
    return evaluate(assets, parameters, risk_aversion, cycle)


async def optimize_async(
    assets: list[Asset],
    risk_aversion: float,
    cycles: int,
    batch_size: int,
    dashboard: OptionalDashboard,
    seed: int,
) -> PortfolioResult:
    rng = random.Random(seed)
    parameter_count = len(assets) * 2
    best_parameters = [rng.uniform(0, 2 * math.pi) for _ in range(parameter_count)]
    best = evaluate(assets, best_parameters, risk_aversion, 0)
    dashboard.log(best, assets)

    cycle = 1
    spread = math.pi
    while cycle <= cycles:
        tasks = []
        for _ in range(batch_size):
            candidate = [
                (value + rng.uniform(-spread, spread)) % (2 * math.pi) for value in best.parameters
            ]
            tasks.append(evaluate_candidate(assets, candidate, risk_aversion, cycle))
            cycle += 1
            if cycle > cycles:
                break

        for result in await asyncio.gather(*tasks):
            if result.score > best.score:
                best = result
                dashboard.log(best, assets)
        spread *= 0.92

    return best


def write_outputs(assets: list[Asset], result: PortfolioResult, capital: float, risk_aversion: float) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    rows = []
    for asset, weight in zip(assets, result.weights):
        cash = capital * weight
        units = cash / asset.current_price if asset.current_price > 0 else 0.0
        rows.append(
            {
                "ticker": asset.ticker,
                "name": asset.name,
                "target_weight": f"{weight:.4f}",
                "target_percent": f"{weight * 100:.2f}%",
                "paper_cash": f"{cash:.2f}",
                "current_price": f"{asset.current_price:.2f}",
                "paper_units": f"{units:.8f}",
                "expected_return_input": f"{asset.expected_return:.4f}",
                "volatility_input": f"{asset.volatility:.4f}",
                "notes": asset.notes,
            }
        )

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Paper Portfolio Summary",
        "",
        "This is educational paper output, not financial advice and not a trading bot.",
        "",
        f"- Paper capital: ${capital:,.2f}",
        f"- Risk aversion: {risk_aversion:.2f}",
        f"- Assets: {len(assets)}",
        f"- Winning cycle: {result.cycle}",
        f"- Estimated portfolio return input: {result.expected_return:.4f}",
        f"- Estimated portfolio risk input: {result.risk:.4f}",
        f"- Sharpe-style score: {result.sharpe:.4f}",
        f"- Objective score: {result.score:.4f}",
        "",
        "## Allocation",
    ]
    for row in rows:
        lines.append(
            f"- {row['ticker']}: {row['target_percent']} | ${row['paper_cash']} | "
            f"{row['paper_units']} paper units"
        )
    lines.extend(
        [
            "",
            "## Engineering Notes",
            "",
            "- Uses a local statevector simulation of a small QNN-shaped ansatz.",
            "- Uses async batched candidate evaluation so the optimizer can be upgraded to real queues later.",
            "- Uses CSV market inputs first; no broker, no auto-trading, no API secrets required.",
            "- Optional `rich` support adds a live terminal dashboard when installed.",
            "- IBM/Qiskit should be an adapter layer after this local workflow is useful.",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


async def run(args: argparse.Namespace) -> None:
    assets = read_assets(DATA_FILE)
    started = time.perf_counter()
    with OptionalDashboard(enabled=not args.no_dashboard) as dashboard:
        result = await optimize_async(
            assets=assets,
            risk_aversion=args.risk_aversion,
            cycles=args.cycles,
            batch_size=args.batch_size,
            dashboard=dashboard,
            seed=args.seed,
        )
    write_outputs(assets, result, args.capital, args.risk_aversion)
    elapsed = time.perf_counter() - started
    print(f"Wrote {OUTPUT_CSV}")
    print(f"Wrote {OUTPUT_MD}")
    print(f"Completed in {elapsed:.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Local multi-asset quantum-inspired paper optimizer.")
    parser.add_argument("--capital", type=float, default=1000.0, help="Paper dollars to allocate.")
    parser.add_argument("--risk-aversion", type=float, default=0.75)
    parser.add_argument("--cycles", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--no-dashboard", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
