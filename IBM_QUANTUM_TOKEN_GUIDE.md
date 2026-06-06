# IBM Quantum Token Guide

An IBM Quantum API token lets a Python program authenticate with IBM Quantum services.

## What It Can Do

- Submit quantum circuits to IBM Quantum backends when your account has access.
- Query available backends and job status.
- Use Qiskit Runtime services for supported workloads.
- Run experiments that compare local simulation results against cloud quantum execution.

## What It Cannot Do

- It cannot guarantee profit.
- It cannot make grants, trades, or legal claims succeed.
- It should not be pasted into public code, screenshots, chats, or GitHub commits.

## Safe Storage

Create a `.env` file in this repo if you later add Qiskit integration:

```text
IBM_QUANTUM_TOKEN=paste_token_here
```

The `.gitignore` file already ignores `.env`.

## Current Repo Status

`quantum_portfolio.py` does not require the IBM token. It runs a local simulation first so the project works before cloud credentials are involved.

After the local workflow is useful, the next step is adding an optional Qiskit adapter:

```powershell
pip install qiskit qiskit-ibm-runtime python-dotenv
```

Then the adapter can read `IBM_QUANTUM_TOKEN` from `.env` and submit the same circuit to IBM.

