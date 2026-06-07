# ⚛️ Quantum Command 52

Quantum Command 52 is a local-first IBM/Qiskit quantum lab with practical resource ledgers attached.

It is **not** a Stripe checkout app, not a real-estate demo, and not a promise that money, benefits, housing, or legal outcomes are guaranteed. It is meant to help organize real links, real notes, and quantum experiments in one place.

📌 Latest cleanup notes: [CHANGELOG_REPO52_CLEANUP.md](CHANGELOG_REPO52_CLEANUP.md)

## 🧭 What This Is For

- ⚛️ Run and inspect IBM/Qiskit quantum experiments.
- 🎯 Rank grant, scholarship, emergency aid, and benefit leads.
- 🏠 Track housing help, legal aid, shelter, and referral resources.
- 🔗 Keep official source links clickable instead of buried in notes.
- 📦 Catalog items with comparable-source links.
- 🧪 Keep paper-market/portfolio experiments clearly marked as research only.

## 🚀 Quick Start

Run these from PowerShell:

```powershell
cd C:\Users\enter\OneDrive\Desktop\Repo52\quantum-command-52
python grants.py rank
python housing_violations.py summarize
python shell_catalog.py estimate
python quantum_portfolio.py --capital 1000
python qml_signal_engine.py --capital 1000
python strict_macro_quantum_v10.py --preflight
```

Outputs are written into the `output` folder.

## 🖥️ Desktop Shortcut

The desktop shortcut named `52` launches the local dashboard.

It points to:

```text
Start-Repo52.ps1
```

That script starts:

- 🔌 Backend API: `http://127.0.0.1:8787`
- 🌐 Frontend dashboard: `http://127.0.0.1:5173`

The shortcut uses the custom icon:

```text
assets/repo52-52.ico
```

## 🧩 Dashboard Tabs

The cleaned app shows:

- 🎓 **Grants**: official aid, scholarship, emergency resource, and benefit links.
- 🏠 **Housing**: shelter, legal aid, counseling, 211, and housing evidence tracking.
- 📦 **Catalog**: item/value research with comparable-source links.
- ⚛️ **Quantum**: IBM/Qiskit and local paper-research tooling.

Removed from the visible app:

- 💳 Billing / Stripe checkout.
- 🏘️ Real-estate Deals demo.
- 💸 Fake `$500,000` command-capital language.

## 📁 Main Files

- `grants.py`: ranks grant and help-resource leads from `data/grants.csv`.
- `housing_violations.py`: writes a housing/help summary from `data/housing_violations.csv`.
- `shell_catalog.py`: estimates catalog values from comparable ranges in `data/shell_items.csv`.
- `quantum_portfolio.py`: local quantum-inspired paper portfolio optimizer.
- `qml_signal_engine.py`: local QML-shaped paper signal engine.
- `strict_macro_quantum_v10.py`: strict IBM/Qiskit/yfinance/Torch pipeline.
- `web-dashboard/`: React dashboard and Python API server.
- `IBM_QUANTUM_TOKEN_GUIDE.md`: IBM Quantum token setup notes.
- `PROJECT_LOG.md`: project history.

## 🔐 IBM Quantum Notes

The strict V10 script expects real enterprise dependencies and IBM Runtime access.

Run a preflight check:

```powershell
py -3.11 strict_macro_quantum_v10.py --preflight
```

Keep secrets in `.env`. Do not commit real IBM, Alpaca, database, or other private keys.

## 📈 Alpaca Paper Research

The strict V10 script can preview Alpaca paper-trading orders. Live trading is intentionally blocked.

Example paper preview:

```powershell
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders
```

Example paper submit:

```powershell
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders --submit-paper-orders
```

## 🌐 Web Dashboard Setup

Install and run manually:

```powershell
cd C:\Users\enter\OneDrive\Desktop\Repo52\quantum-command-52\web-dashboard
npm install
py -3.11 -m pip install -r requirements.txt
py -3.11 server.py
```

In a second PowerShell window:

```powershell
cd C:\Users\enter\OneDrive\Desktop\Repo52\quantum-command-52\web-dashboard
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## 🧪 Local Demo Mode

The shortcut starts the backend with:

```text
REPO52_DEMO_MODE=true
APP_ENV=development
REQUIRE_ALEMBIC_MIGRATIONS=false
```

That mode skips PostgreSQL and uses the ignored local database:

```text
web-dashboard/data.db
```

Delete that ignored file only if you want to reset local demo rows.

## 🗄️ Production Database

For non-demo backend runs, set `.env` values such as:

```text
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/quantum_command_52
DATABASE_POOL_MIN=1
DATABASE_POOL_MAX=10
JWT_SECRET=replace-with-at-least-32-random-characters
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
RATE_LIMIT_AUTH_PER_MINUTE=12
RATE_LIMIT_API_PER_MINUTE=120
```

Run migrations from PowerShell:

```powershell
cd C:\Users\enter\OneDrive\Desktop\Repo52\quantum-command-52\web-dashboard
py -3.11 -m alembic upgrade head
```

## 🐳 Docker

Copy the production example and set strong secrets:

```powershell
Copy-Item .env.production.example .env.production
```

Start the stack:

```powershell
docker compose --env-file .env.production up --build
```

Services:

- App and API: `http://127.0.0.1:8080`
- PostgreSQL: internal Docker network with persistent `postgres_data` volume
- Migration job: `migrate` runs `alembic upgrade head`

## ✅ Use It For Real

1. Open the CSV files in `data`.
2. Add real opportunities, resources, evidence, or items.
3. Keep official URLs in the `source_url` columns.
4. Run the matching script.
5. Use the generated Markdown/CSV files in `output`.

## 🚧 Limits

- No script guarantees a grant, benefit, settlement, or sale price.
- No script is legal advice.
- No script is financial advice.
- No script should receive private documents from strangers or random websites.
- Housing/legal summaries are organizers; talk to a qualified legal aid or tenant-rights office for action.
