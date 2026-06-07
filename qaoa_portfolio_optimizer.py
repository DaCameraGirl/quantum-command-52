from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from qiskit.circuit.library import QAOAAnsatz
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit.quantum_info import SparsePauliOp


@dataclass(frozen=True)
class QaoaPortfolioResult:
    tickers: list[str]
    qaoa_bits: str
    exact_bits: str
    qaoa_cost: float
    exact_cost: float
    matched_exact: bool
    selected_tickers: list[str]
    counts: dict[str, int]
    optimizer_energy: float


def build_qubo(mu: np.ndarray, sigma: np.ndarray, budget: int, risk_factor: float, penalty: float) -> np.ndarray:
    """Build Q for min -mu.x + q*x.T*sigma*x + penalty*(sum(x)-budget)^2."""
    n = len(mu)
    q_matrix = risk_factor * np.array(sigma, dtype=float)
    q_matrix += penalty * np.ones((n, n))
    for index in range(n):
        q_matrix[index, index] += -float(mu[index])
        q_matrix[index, index] += -2 * penalty * budget
    return q_matrix


def qubo_to_ising(q_matrix: np.ndarray) -> SparsePauliOp:
    """Exact QUBO to Ising transform using x_i = (I - Z_i) / 2."""
    n = q_matrix.shape[0]
    identity = SparsePauliOp.from_list([("I" * n, 1.0)])

    def selection_operator(index: int) -> SparsePauliOp:
        return 0.5 * identity - 0.5 * SparsePauliOp.from_sparse_list([("Z", [index], 1.0)], num_qubits=n)

    operator = SparsePauliOp.from_list([("I" * n, 0.0)])
    for row in range(n):
        for column in range(n):
            value = float(q_matrix[row, column])
            if value != 0.0:
                operator += value * (selection_operator(row) @ selection_operator(column))
    return operator.simplify()


def portfolio_energy(bits: str, q_matrix: np.ndarray) -> float:
    vector = np.array([int(bit) for bit in bits], dtype=float)
    return float(vector @ q_matrix @ vector)


def brute_force_optimum(q_matrix: np.ndarray) -> tuple[str, float]:
    n = q_matrix.shape[0]
    best_bits = ""
    best_energy = np.inf
    for combo in itertools.product([0, 1], repeat=n):
        bits = "".join(map(str, combo))
        current_energy = portfolio_energy(bits, q_matrix)
        if current_energy < best_energy:
            best_energy = current_energy
            best_bits = bits
    return best_bits, float(best_energy)


def run_qaoa(
    cost_operator: SparsePauliOp,
    q_matrix: np.ndarray,
    *,
    reps: int = 2,
    seed: int = 7,
    restarts: int = 3,
    maxiter: int = 200,
    shots: int = 4096,
) -> tuple[str, dict[str, int], float]:
    ansatz = QAOAAnsatz(cost_operator, reps=reps)
    ansatz.measure_all()
    circuit = ansatz.remove_final_measurements(inplace=False)
    estimator = StatevectorEstimator(seed=seed)

    def expectation_value(theta: np.ndarray) -> float:
        result = estimator.run([(circuit, cost_operator, theta)]).result()
        return float(result[0].data.evs)

    rng = np.random.default_rng(seed)
    best_output = None
    for _ in range(restarts):
        initial_parameters = rng.uniform(0, 2 * np.pi, circuit.num_parameters)
        output = minimize(expectation_value, initial_parameters, method="COBYLA", options={"maxiter": maxiter})
        if best_output is None or output.fun < best_output.fun:
            best_output = output

    if best_output is None:
        raise RuntimeError("QAOA optimizer did not return a result.")

    measured = ansatz.assign_parameters(best_output.x)
    sampler = StatevectorSampler(seed=seed)
    counts = sampler.run([measured], shots=shots).result()[0].data.meas.get_counts()
    candidates = {bitstring[::-1]: count for bitstring, count in counts.items()}
    best_bits = min(candidates, key=lambda bits: portfolio_energy(bits, q_matrix))
    return best_bits, candidates, float(best_output.fun)


def optimize_portfolio_qaoa(
    tickers: list[str],
    mu: np.ndarray,
    sigma: np.ndarray,
    *,
    budget: int | None = None,
    risk_factor: float = 0.5,
    penalty: float = 2.0,
    reps: int = 2,
    seed: int = 7,
    restarts: int = 3,
    maxiter: int = 200,
    shots: int = 4096,
) -> QaoaPortfolioResult:
    if budget is None:
        budget = max(1, min(len(tickers), round(len(tickers) * 0.6)))
    if not 1 <= budget <= len(tickers):
        raise ValueError("budget must be between 1 and the number of tickers")

    q_matrix = build_qubo(mu, sigma, budget, risk_factor, penalty)
    cost_operator = qubo_to_ising(q_matrix)
    qaoa_bits, counts, optimizer_energy = run_qaoa(
        cost_operator,
        q_matrix,
        reps=reps,
        seed=seed,
        restarts=restarts,
        maxiter=maxiter,
        shots=shots,
    )
    exact_bits, exact_cost = brute_force_optimum(q_matrix)
    qaoa_cost = portfolio_energy(qaoa_bits, q_matrix)
    selected_tickers = [ticker for ticker, bit in zip(tickers, qaoa_bits) if bit == "1"]
    return QaoaPortfolioResult(
        tickers=tickers,
        qaoa_bits=qaoa_bits,
        exact_bits=exact_bits,
        qaoa_cost=qaoa_cost,
        exact_cost=exact_cost,
        matched_exact=qaoa_bits == exact_bits,
        selected_tickers=selected_tickers,
        counts=counts,
        optimizer_energy=optimizer_energy,
    )


def demo_inputs() -> tuple[list[str], np.ndarray, np.ndarray]:
    tickers = ["A", "B", "C", "D", "E"]
    mu = np.array([0.12, 0.10, 0.07, 0.15, 0.09], dtype=float)
    rng = np.random.default_rng(1)
    raw = rng.normal(0, 1, (5, 5))
    sigma = (raw @ raw.T) / 5 + np.eye(5) * 0.02
    return tickers, mu, sigma


def format_selection(bits: str, tickers: list[str], q_matrix: np.ndarray) -> str:
    selected = [tickers[index] for index, bit in enumerate(bits) if bit == "1"]
    return f"{bits} -> {selected} (cost {portfolio_energy(bits, q_matrix):+.4f})"


if __name__ == "__main__":
    demo_tickers, demo_mu, demo_sigma = demo_inputs()
    result = optimize_portfolio_qaoa(demo_tickers, demo_mu, demo_sigma, budget=3, reps=2, maxiter=80, shots=1024)
    q_matrix = build_qubo(demo_mu, demo_sigma, budget=3, risk_factor=0.5, penalty=2.0)
    print("QAOA pick :", format_selection(result.qaoa_bits, demo_tickers, q_matrix))
    print("Exact pick:", format_selection(result.exact_bits, demo_tickers, q_matrix))
    print("Match     :", result.matched_exact)
