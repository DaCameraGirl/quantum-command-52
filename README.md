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
- `web-dashboard/` is a React/Tailwind/Recharts command center with PostgreSQL-backed user authentication, portfolio telemetry, grants, housing evidence, physical inventory, and real estate transaction pipeline views.
- `PROJECT_LOG.md` records the release history for each major GitHub push.

## Alpaca Paper Trading

The strict V10 script can create Alpaca paper-trading order previews and, with an explicit flag, submit paper market buy orders. Live trading mode is intentionally blocked.

Add paper credentials to `.env`:

```text
ALPACA_API_KEY=your_paper_key
ALPACA_SECRET_KEY=your_paper_secret
ALPACA_PAPER=true
```

Preview paper orders:

```powershell
py -3.11 strict_macro_quantum_v10.py --bankroll 500000 --preview-alpaca-orders
```

Submit paper orders:

```powershell
py -3.11 strict_macro_quantum_v10.py --bankroll 500000 --preview-alpaca-orders --submit-paper-orders
```

## Web Dashboard

Install and run the dashboard:

```powershell
cd C:\Users\enter\angela-practical-funding-toolkit\web-dashboard
npm install
py -3.11 -m pip install -r requirements.txt
py -3.11 server.py
```

In a second PowerShell window:

```powershell
cd C:\Users\enter\angela-practical-funding-toolkit\web-dashboard
npm run dev
```

Open `http://127.0.0.1:5173`.

The API now requires PostgreSQL. Set this in the repo `.env` before starting `server.py`:

```text
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/quantum_command_52
DATABASE_POOL_MIN=1
DATABASE_POOL_MAX=10
JWT_SECRET=replace-with-at-least-32-random-characters
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
RATE_LIMIT_AUTH_PER_MINUTE=12
RATE_LIMIT_API_PER_MINUTE=120
```

The backend validates runtime configuration through `web-dashboard/app_config.py` using Pydantic. Database URLs and JWT secrets are stored as secret fields, redacted in normal representation, and rejected early if required values are missing or malformed.

### Local Demo Shortcut

The desktop shortcut and `Start-Repo52.ps1` start the backend with:

```text
REPO52_DEMO_MODE=true
APP_ENV=development
REQUIRE_ALEMBIC_MIGRATIONS=false
```

That mode skips the PostgreSQL socket connection and serves thread-safe in-memory demo data for portfolio, grants, housing, inventory, and real estate transactions. It is for local dashboard preview only; it does not persist changes after the backend window closes. `server.py` rejects demo mode when `APP_ENV=production`.

## Stripe Webhooks

Set Stripe billing secrets before enabling subscription billing:

```text
STRIPE_SECRET_KEY=sk_live_replace_with_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_replace_with_stripe_endpoint_secret
STRIPE_SUCCESS_URL=https://your-domain.example/?checkout=success
STRIPE_CANCEL_URL=https://your-domain.example/?checkout=cancelled
STRIPE_PRICE_STARTER=price_replace_with_starter_price_id
STRIPE_PRICE_PRO=price_replace_with_pro_price_id
STRIPE_PRICE_ENTERPRISE=price_replace_with_enterprise_price_id
```

The backend exposes authenticated `POST /api/stripe/checkout`. The browser sends a tier (`starter`, `pro`, or `enterprise`), the server maps it to a configured Stripe Price ID, and Stripe returns a Checkout redirect URL. The browser never chooses arbitrary price IDs.

The React dashboard includes a Billing tab that calls this endpoint and redirects the signed-in user to Stripe's hosted Checkout page.

The backend exposes `POST /api/stripe/webhook`. It verifies the `Stripe-Signature` header, records every accepted event in `stripe_webhook_events`, and updates `billing_accounts` for checkout, subscription, payment-failed, and subscription-paused events.

## API Contract

The API contract lives at `web-dashboard/openapi.json` and is served by the backend at:

- `http://127.0.0.1:8787/openapi.json`
- `http://127.0.0.1:8787/api/openapi.json`

Authenticated routes accept either the `access_token` JWT cookie or a bearer JWT in the `Authorization` header. Every JSON response includes an `X-Request-ID` correlation header for tracing logs back to a specific request.

## Database Migrations

The backend still has a startup schema initializer for local development compatibility, but production mode is Alembic-only. When `APP_ENV=production` or `REQUIRE_ALEMBIC_MIGRATIONS=true`, `server.py` skips the legacy `init_db()` fallback and refuses to boot unless the expected Alembic revision is present.

Run migrations from PowerShell:

```powershell
cd C:\Users\enter\angela-practical-funding-toolkit\web-dashboard
py -3.11 -m alembic upgrade head
```

Create the next migration after a schema change:

```powershell
py -3.11 -m alembic revision -m "describe schema change"
```

Seed the real estate transaction board for registered users:

```powershell
cd C:\Users\enter\angela-practical-funding-toolkit\web-dashboard
py -3.11 seed_transactions.py
```

Seed one user by email:

```powershell
py -3.11 seed_transactions.py --email user@example.com
```

## Docker Deployment

Copy the production example and set strong secrets:

```powershell
Copy-Item .env.production.example .env.production
```

Then start the full local stack:

```powershell
docker compose --env-file .env.production up --build
```

Services:

- App and API: `http://127.0.0.1:8080`
- PostgreSQL: internal Docker network with persistent `postgres_data` volume
- Migration job: `migrate` runs `alembic upgrade head` before the app starts

The production `Dockerfile` is a monorepo multi-stage build. Stage 1 compiles the React/Vite dashboard; Stage 2 installs the Python API dependencies, copies the compiled dashboard assets, and serves both the frontend and `/api/*` routes from one hardened runtime container.

The Vite production build uses manual Rollup chunks for React, Recharts/D3, Lucide icons, and remaining vendor modules so dashboard bundles stay split by dependency family.

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
