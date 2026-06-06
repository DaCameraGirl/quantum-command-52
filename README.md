# Angela Practical Funding Toolkit

This repo replaces the fake "quantum grant" code with practical local tools.

It does not guarantee money, file legal claims, or appraise collectibles. It helps you organize real opportunities, evidence, and comparable sale data so you can take the next useful step.

## Quick Start

Run these from PowerShell:

```powershell
cd C:\Users\enter\angela-practical-funding-toolkit
python grants.py rank
python housing_violations.py summarize
python shell_catalog.py estimate
python quantum_portfolio.py --capital 1000
python qml_signal_engine.py --capital 1000
python strict_macro_quantum_v10.py --preflight
```

The scripts write results into the `output` folder.

## Files

- `grants.py` ranks grant/scholarship/emergency aid opportunities from `data/grants.csv`.
- `housing_violations.py` summarizes unresolved housing issues from `data/housing_violations.csv`.
- `shell_catalog.py` estimates collectible ranges only from comparable sale values you provide in `data/shell_items.csv`.
- `quantum_portfolio.py` runs a local quantum-inspired paper portfolio optimizer from `data/portfolio_assets.csv`.
- `qml_signal_engine.py` runs a local QML-shaped paper signal engine from `data/market_features.csv`.
- `strict_macro_quantum_v10.py` is the hard-dependency IBM/Qiskit/yfinance/Torch version. It fails fast if the enterprise stack, `.env` token, live market data, or IBM Runtime connection is unavailable.
- `web-dashboard/` is a React/Tailwind/Recharts dashboard with SQLite-backed user authentication and per-user paper portfolio telemetry.

## Web Dashboard

Install and run the dashboard:

```powershell
cd C:\Users\enter\angela-practical-funding-toolkit\web-dashboard
npm install
py -3.11 server.py
```

In a second PowerShell window:

```powershell
cd C:\Users\enter\angela-practical-funding-toolkit\web-dashboard
npm run dev
```

Open `http://127.0.0.1:5173`.

## How To Use For Real

1. Open the CSV files in `data`.
2. Replace the sample rows with real opportunities, violations, or items.
3. Run the matching script.
4. Use the generated files in `output` as your call list, application tracker, or evidence packet.

## Important Limits

- No script can guarantee a grant, settlement, or sale price.
- No script is financial advice or a trading bot.
- Do not send private documents to random websites.
- For legal action, use the housing summary as an organizer and talk to a qualified tenant/legal aid office.
