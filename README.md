<p align="center">
  <img src="docs/assets/readme-hero.svg" alt="Quantum Command 52 — IBM/Qiskit lab with resource ledgers" width="100%"/>
</p>

# Quantum Command 52

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/🇺🇸_English-38bdf8?style=for-the-badge&labelColor=070b12" alt="English"/></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/🇪🇸_Español-132033?style=for-the-badge&labelColor=070b12" alt="Español"/></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/🇫🇷_Français-132033?style=for-the-badge&labelColor=070b12" alt="Français"/></a>
  <a href="README.de.md"><img src="https://img.shields.io/badge/🇩🇪_Deutsch-132033?style=for-the-badge&labelColor=070b12" alt="Deutsch"/></a>
  <a href="README.pt-BR.md"><img src="https://img.shields.io/badge/🇧🇷_Português-132033?style=for-the-badge&labelColor=070b12" alt="Português"/></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/🇨🇳_中文-132033?style=for-the-badge&labelColor=070b12" alt="中文"/></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/🇯🇵_日本語-132033?style=for-the-badge&labelColor=070b12" alt="日本語"/></a>
  <a href="README.ko.md"><img src="https://img.shields.io/badge/🇰🇷_한국어-132033?style=for-the-badge&labelColor=070b12" alt="한국어"/></a>
  <a href="README.it.md"><img src="https://img.shields.io/badge/🇮🇹_Italiano-132033?style=for-the-badge&labelColor=070b12" alt="Italiano"/></a>
  <a href="README.ar.md"><img src="https://img.shields.io/badge/🇸🇦_العربية-132033?style=for-the-badge&labelColor=070b12" alt="العربية"/></a>
</p>

<p align="center">
  <a href="https://dacameragirl.github.io/quantum-command-52/"><img src="https://img.shields.io/badge/🌐_Live_Demo-38bdf8?style=for-the-badge&labelColor=070b12" alt="Live demo"/></a>
  <a href="https://dacameragirl.github.io/links/"><img src="https://img.shields.io/badge/🔗_Project_Hub-132033?style=for-the-badge&labelColor=070b12" alt="Project hub"/></a>
  <img src="https://img.shields.io/badge/Qiskit-IBM-6929C4?style=for-the-badge&logo=qiskit&logoColor=white" alt="Qiskit"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=070b12" alt="Python"/>
  <img src="https://img.shields.io/badge/React-149ECA?style=for-the-badge&logo=react&logoColor=white&labelColor=070b12" alt="React"/>
  <img src="https://img.shields.io/badge/Pages_snapshot-38bdf8?style=for-the-badge&labelColor=050a12" alt="Pages snapshot"/>
</p>

<p align="center">
  <img src="docs/assets/quantum-circuit.svg" alt="Animated quantum circuit — qubits, gates, entanglement" width="620"/>
</p>

**Local-first IBM/Qiskit quantum lab with practical resource ledgers attached.**

It is **not** a Stripe checkout app, not a real-estate demo, and not a promise that money, benefits, housing, or legal outcomes are guaranteed. It helps organize real links, real notes, and quantum experiments in one place.

<p align="center">
  <img src="docs/assets/readme-status.svg" alt="Local-first quantum lab — not billing, not guaranteed outcomes" width="100%"/>
</p>

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## Repo vs live

| What | URL |
|---|---|
| **Live snapshot** (GitHub Pages, CSV export) | [dacameragirl.github.io/quantum-command-52](https://dacameragirl.github.io/quantum-command-52/) |
| **GitHub repo** | [github.com/DaCameraGirl/quantum-command-52](https://github.com/DaCameraGirl/quantum-command-52) |
| **Full dashboard** (local API + Vite) | Desktop shortcut **52** → `Start-Repo52.ps1` |
| **Project hub** | [dacameragirl.github.io/links](https://dacameragirl.github.io/links/) |

Latest cleanup notes: [CHANGELOG_REPO52_CLEANUP.md](CHANGELOG_REPO52_CLEANUP.md)

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## What this is for

| Area | What it does |
|---|---|
| **Quantum** | Run and inspect IBM/Qiskit experiments; QAOA, QML, paper portfolio research |
| **Grants** | Rank grant, scholarship, emergency aid, and benefit leads |
| **Housing** | Track shelter, legal aid, counseling, 211, and housing evidence |
| **Catalog** | Item/value research with comparable-source links |
| **Links** | Keep official `source_url` columns clickable — not buried in notes |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## Quick start

From the repo root in PowerShell:

```powershell
python grants.py rank
python housing_violations.py summarize
python shell_catalog.py estimate
python quantum_portfolio.py --capital 1000
python qml_signal_engine.py --capital 1000
python strict_macro_quantum_v10.py --preflight
```

Outputs land in the `output` folder.

## Desktop shortcut

The desktop shortcut named **52** launches the local dashboard via `Start-Repo52.ps1`.

| Surface | URL |
|---|---|
| Backend API | http://127.0.0.1:8787 |
| Frontend dashboard | http://127.0.0.1:5173 |
| Icon | `assets/repo52-52.ico` |

## Dashboard tabs

| Tab | Content |
|---|---|
| **Grants** | Official aid, scholarship, emergency resource, and benefit links |
| **Housing** | Shelter, legal aid, counseling, 211, housing evidence tracking |
| **Catalog** | Item/value research with comparable-source links |
| **Quantum** | IBM/Qiskit and local paper-research tooling |

**Removed from the visible app:** Billing/Stripe checkout · Real-estate Deals demo · Fake `$500,000` command-capital language

## Main files

| File | Role |
|---|---|
| `grants.py` | Ranks grant and help-resource leads from `data/grants.csv` |
| `housing_violations.py` | Housing/help summary from `data/housing_violations.csv` |
| `shell_catalog.py` | Catalog value estimates from `data/shell_items.csv` |
| `quantum_portfolio.py` | Local quantum-inspired paper portfolio optimizer |
| `qml_signal_engine.py` | Local QML-shaped paper signal engine |
| `strict_macro_quantum_v10.py` | Strict IBM/Qiskit/yfinance/Torch pipeline |
| `web-dashboard/` | React dashboard + Python API server |
| `IBM_QUANTUM_TOKEN_GUIDE.md` | IBM Quantum token setup |
| `PROJECT_LOG.md` | Project history |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## IBM Quantum

The strict V10 script expects enterprise dependencies and IBM Runtime access.

```powershell
py -3.11 strict_macro_quantum_v10.py --preflight
```

Keep secrets in `.env`. Do not commit IBM, Alpaca, database, or other private keys.

### Alpaca paper research

Live trading is intentionally blocked. Paper preview/submit only:

```powershell
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders --submit-paper-orders
```

## Web dashboard setup

```powershell
cd web-dashboard
npm install
py -3.11 -m pip install -r requirements.txt
py -3.11 server.py
```

Second terminal:

```powershell
cd web-dashboard
npm run dev
```

Open http://127.0.0.1:5173

## Data source of truth

Grant, housing, and catalog dashboard stats come from repo-root CSV files:

| File | Dashboard tab |
|---|---|
| `data/grants.csv` | Grants |
| `data/housing_violations.csv` | Housing |
| `data/shell_items.csv` | Catalog |

The matching CLI scripts (`grants.py`, `housing_violations.py`, `shell_catalog.py`) read the same files and write Markdown/CSV summaries to `output/`.

| Surface | How stats load |
|---|---|
| **Desktop shortcut 52** | Live read of `data/*.csv` on each API start (`REPO52_DATA_SOURCE=csv`) |
| **GitHub Pages** | Dated JSON snapshot in `web-dashboard/public/demo/` — regenerate before deploy |

Regenerate the Pages snapshot:

```powershell
py -3.11 web-dashboard/scripts/export_pages_demo.py
```

Check live counts locally:

```powershell
curl http://127.0.0.1:8787/api/meta
```

## Local SQLite mode

The shortcut starts the backend with:

```text
REPO52_DEMO_MODE=true
REPO52_DATA_SOURCE=csv
APP_ENV=development
REQUIRE_ALEMBIC_MIGRATIONS=false
```

Uses ignored local DB: `web-dashboard/data.db` for auth/session cache — delete to reset local edits. Ledger rows reload from CSV on restart when `REPO52_DATA_SOURCE=csv`.

Set `REPO52_DATA_SOURCE=seed` only if you need the old in-memory seed rows for testing.

## Production database

```text
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/quantum_command_52
DATABASE_POOL_MIN=1
DATABASE_POOL_MAX=10
JWT_SECRET=replace-with-at-least-32-random-characters
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
RATE_LIMIT_AUTH_PER_MINUTE=12
RATE_LIMIT_API_PER_MINUTE=120
```

```powershell
cd web-dashboard
py -3.11 -m alembic upgrade head
```

## Docker

```powershell
Copy-Item .env.production.example .env.production
docker compose --env-file .env.production up --build
```

| Service | URL / role |
|---|---|
| App + API | http://127.0.0.1:8080 |
| PostgreSQL | Internal Docker network, `postgres_data` volume |
| Migrate job | `alembic upgrade head` |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## Use it for real

1. Open the CSV files in `data`.
2. Add real opportunities, resources, evidence, or items.
3. Keep official URLs in `source_url` columns.
4. Run the matching script.
5. Use generated Markdown/CSV in `output`.

## Limits

- No script guarantees a grant, benefit, settlement, or sale price.
- No script is legal or financial advice.
- Do not upload private documents from strangers or random websites.
- Housing/legal summaries are organizers — talk to qualified legal aid for action.

## Contributors

- **Angela Hudson** ([DaCameraGirl](https://github.com/DaCameraGirl)) — product direction, resource data, testing
- **Claude** — dashboard cleanup, Pages deploy, quantum scripts

## License

Copyright (c) 2026 Angela Nelson. All Rights Reserved.

Public for viewing only. No permission to use, copy, modify, publish, distribute, sell, sublicense, or create derivative works without prior written permission.

Full terms: [LICENSE](LICENSE)