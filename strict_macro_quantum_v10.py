from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REQUIRED_PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "torch": "torch",
    "yfinance": "yfinance",
    "dotenv": "python-dotenv",
    "qiskit": "qiskit",
    "qiskit_ibm_runtime": "qiskit-ibm-runtime",
    "rich": "rich",
    "openpyxl": "openpyxl",
}


def fail(message: str) -> None:
    print(f"[STRICT-QML-FAIL] {message}")
    raise SystemExit(1)


def import_required_stack() -> dict[str, object]:
    modules: dict[str, object] = {}
    missing: list[str] = []
    for module_name, package_name in REQUIRED_PACKAGES.items():
        try:
            modules[module_name] = __import__(module_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        fail(
            "Missing required packages: "
            + ", ".join(sorted(set(missing)))
            + "\nInstall with: pip install -r requirements-enterprise.txt"
        )
    return modules


STACK = import_required_stack()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
import yfinance as yf  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from qiskit import QuantumCircuit  # noqa: E402
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn  # noqa: E402
from rich.table import Table  # noqa: E402


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
WORKBOOK = OUTPUT_DIR / "ANGELAS_QUANTUM_EMPIRE_V10.xlsx"
ENV_FILE = ROOT / ".env"
console = Console()


class StrictQuantumNeuralLayer(nn.Module):
    def __init__(self, num_qubits: int, backend_name: str | None):
        super().__init__()
        self.num_qubits = num_qubits

        token = os.getenv("IBM_QUANTUM_TOKEN", "").strip()
        instance = os.getenv("IBM_QUANTUM_INSTANCE", "").strip()
        if not token:
            fail("IBM_QUANTUM_TOKEN is missing or blank in .env.")
        if not instance:
            fail(
                "IBM_QUANTUM_INSTANCE is missing or blank in .env. "
                "Add the IBM Quantum service CRN or service instance name."
            )

        try:
            self.service = QiskitRuntimeService(
                channel="ibm_quantum_platform",
                token=token,
                instance=instance,
            )
            self.backend = self._select_backend(backend_name)
            self.sampler = SamplerV2(self.backend)
        except Exception as exc:
            fail(f"IBM Quantum Runtime initialization failed: {type(exc).__name__}: {exc}")

    def _select_backend(self, backend_name: str | None):
        if backend_name:
            return self.service.backend(backend_name)

        preferred = ["ibmq_qasm_simulator", "ibm_qasm_simulator"]
        for name in preferred:
            try:
                return self.service.backend(name)
            except Exception:
                pass

        backends = self.service.backends(simulator=True, operational=True)
        if not backends:
            fail("No operational IBM simulator backend is available to this account.")
        return backends[0]

    def compile_quantum_graph(self, features: np.ndarray, weights: np.ndarray) -> QuantumCircuit:
        circuit = QuantumCircuit(self.num_qubits)

        for index in range(self.num_qubits):
            circuit.h(index)
            circuit.ry(float(features[index]), index)

        for index in range(self.num_qubits - 1):
            circuit.cx(index, index + 1)
        circuit.cx(self.num_qubits - 1, 0)

        for index in range(self.num_qubits):
            circuit.rz(float(weights[index]), index)

        circuit.measure_all()
        return circuit

    def forward(self, x: torch.Tensor, weights_tensor: torch.Tensor) -> torch.Tensor:
        classical_features = x.detach().cpu().numpy()[0]
        quantum_weights = weights_tensor.detach().cpu().numpy()
        circuit = self.compile_quantum_graph(classical_features, quantum_weights)

        job = self.sampler.run([circuit], shots=4096)
        result = job.result()
        counts = result[0].data.meas.get_counts()
        total_shots = sum(counts.values())
        if total_shots <= 0:
            fail("IBM Sampler returned zero measurement shots.")

        output_array = np.zeros(self.num_qubits)
        for state, count in counts.items():
            for index in range(self.num_qubits):
                if state[self.num_qubits - 1 - index] == "1":
                    output_array[index] += count

        return torch.tensor(output_array / total_shots, dtype=torch.float32)


class MacroQuantumEmpireV10:
    def __init__(self, assets: list[str], bankroll: float, backend_name: str | None):
        if len(assets) < 2:
            fail("At least two assets are required.")

        self.assets = [asset.strip().upper() for asset in assets]
        self.bankroll = bankroll
        self.num_assets = len(self.assets)

        console.print(
            Panel(
                "[bold magenta]STRICT QUANTUM MACRO-INTELLIGENCE MATRIX v10[/bold magenta]",
                border_style="magenta",
            )
        )

        self.classical_network = nn.Sequential(
            nn.Linear(self.num_assets * 2, self.num_assets * 4),
            nn.Tanh(),
            nn.Linear(self.num_assets * 4, self.num_assets),
        )
        self.quantum_layer = StrictQuantumNeuralLayer(
            num_qubits=self.num_assets,
            backend_name=backend_name,
        )
        self.quantum_weights = nn.Parameter(torch.randn(self.num_assets, requires_grad=True))

    def ingest_live_wall_street_tensors(self, period: str):
        returns_vector: list[float] = []
        volatility_vector: list[float] = []
        current_prices: list[float] = []

        for ticker in self.assets:
            console.print(f"[cyan]Fetching {ticker} from yfinance...[/cyan]")
            history = yf.Ticker(ticker).history(period=period)
            if history.empty or "Close" not in history:
                fail(f"yfinance returned empty close-price history for {ticker}.")

            daily_returns = history["Close"].pct_change().dropna()
            if daily_returns.empty:
                fail(f"Not enough return history for {ticker}.")

            annualized_return = float(daily_returns.mean() * 252)
            annualized_volatility = float(daily_returns.std() * np.sqrt(252))
            current_price = float(history["Close"].iloc[-1])
            if current_price <= 0:
                fail(f"Invalid latest market price for {ticker}: {current_price}")

            returns_vector.append(annualized_return)
            volatility_vector.append(annualized_volatility)
            current_prices.append(current_price)

        raw_features = np.concatenate([returns_vector, volatility_vector])
        feature_tensor = torch.tensor([raw_features], dtype=torch.float32)
        return feature_tensor, returns_vector, volatility_vector, current_prices

    def execute_intelligence_pipeline(self, period: str):
        features, returns, volatilities, prices = self.ingest_live_wall_street_tensors(period)
        compressed_signals = self.classical_network(features)
        quantum_signals = self.quantum_layer.forward(compressed_signals, self.quantum_weights)
        allocations = torch.softmax(quantum_signals, dim=0).detach().numpy()
        return allocations, returns, volatilities, prices

    def compile_multi_sheet_system_ledger(
        self,
        weights: np.ndarray,
        returns: list[float],
        volatilities: list[float],
        prices: list[float],
    ) -> None:
        OUTPUT_DIR.mkdir(exist_ok=True)

        paper_allocations = []
        for index, asset in enumerate(self.assets):
            cash_outlay = self.bankroll * float(weights[index])
            volume = cash_outlay / prices[index]
            paper_allocations.append(
                {
                    "Asset_Ticker": asset,
                    "Quantum_Network_Weight": f"{weights[index] * 100:.2f}%",
                    "Paper_Capital_Allocation_USD": round(cash_outlay, 2),
                    "Live_Market_Price": round(prices[index], 2),
                    "Calculated_Paper_Order_Volume": round(volume, 6),
                }
            )

        telemetry = []
        for index, asset in enumerate(self.assets):
            telemetry.append(
                {
                    "Asset_Ticker": asset,
                    "Expected_Annualized_Return": f"{returns[index] * 100:.2f}%",
                    "Annualized_Volatility_Risk": f"{volatilities[index] * 100:.2f}%",
                    "IBM_Backend": self.quantum_layer.backend.name,
                }
            )

        with pd.ExcelWriter(WORKBOOK, engine="openpyxl") as writer:
            pd.DataFrame(paper_allocations).to_excel(writer, sheet_name="Paper Allocations", index=False)
            pd.DataFrame(telemetry).to_excel(writer, sheet_name="Market Intelligence Log", index=False)

        table = Table(title="[bold green]STRICT V10 PAPER LEDGER[/bold green]")
        table.add_column("Asset", style="cyan")
        table.add_column("Weight", style="magenta")
        table.add_column("Paper Capital", style="green")
        table.add_column("Annual Return", style="yellow")
        for index, asset in enumerate(self.assets):
            table.add_row(
                asset,
                f"{weights[index] * 100:.2f}%",
                f"${self.bankroll * float(weights[index]):,.2f}",
                f"{returns[index] * 100:.2f}%",
            )
        console.print(table)
        console.print(f"[bold green]Workbook written: {WORKBOOK}[/bold green]")


def preflight() -> None:
    if not ENV_FILE.exists():
        fail(f"Missing .env file at {ENV_FILE}")
    token = ""
    for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("IBM_QUANTUM_TOKEN="):
            token = line.split("=", 1)[1].strip()
            break
    if not token:
        fail("IBM_QUANTUM_TOKEN is missing or blank in .env.")
    instance = ""
    for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("IBM_QUANTUM_INSTANCE="):
            instance = line.split("=", 1)[1].strip()
            break
    if not instance:
        fail("IBM_QUANTUM_INSTANCE is missing or blank in .env.")
    console.print("[green]Strict dependency imports passed.[/green]")
    console.print("[green]IBM_QUANTUM_TOKEN is present in .env. Token was not printed.[/green]")
    console.print("[green]IBM_QUANTUM_INSTANCE is present in .env. Instance was not printed.[/green]")


def main() -> None:
    load_dotenv(dotenv_path=ENV_FILE)

    parser = argparse.ArgumentParser(description="Strict IBM/Qiskit/YFinance QML macro matrix.")
    parser.add_argument("--bankroll", type=float, default=500000.0)
    parser.add_argument("--assets", default="AAPL,MSFT,NVDA,AMZN")
    parser.add_argument("--period", default="60d")
    parser.add_argument("--backend", default=None)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()

    if args.preflight:
        preflight()
        return

    assets = [asset.strip() for asset in args.assets.split(",") if asset.strip()]
    engine = MacroQuantumEmpireV10(
        assets=assets,
        bankroll=args.bankroll,
        backend_name=args.backend,
    )

    with Progress(
        SpinnerColumn(spinner_name="dots12"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        transient=True,
    ) as progress:
        task = progress.add_task("Streaming yfinance data and running IBM quantum sampler...", total=100)
        weights, returns, volatilities, prices = engine.execute_intelligence_pipeline(args.period)
        progress.update(task, advance=100)

    engine.compile_multi_sheet_system_ledger(weights, returns, volatilities, prices)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        fail("Interrupted by user.")
