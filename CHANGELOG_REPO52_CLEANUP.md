# Repo 52 Cleanup Notes

Date: 2026-06-07

This page records the cleanup pass so it is easy to see what changed and where to look if something needs to be restored later.

## Purpose

Quantum Command 52 is being cleaned back into a quantum-first local tool:

- Keep the IBM/Qiskit quantum work.
- Keep real, clickable resource ledgers for grants, housing help, legal aid, and catalog research.
- Remove or hide fake SaaS, Stripe checkout, real-estate demo, and inflated paper-capital language.

## Kept

- IBM/Qiskit scripts and quantum runtime guide.
- Quantum tab in the dashboard.
- Grant/help resource ledger.
- Housing help and evidence ledger.
- Catalog/source-link ledger.
- Local demo launcher.

## Removed From The Visible App

- Billing tab.
- Stripe subscription checkout screen.
- Real-estate Deals tab.
- `$500,000` command-capital display.
- "Macro Asset Command Center" login/header wording.
- "Enter command" login button wording.

## Added Or Changed

- Desktop shortcut named `52`.
- Custom `52` icon at `assets/repo52-52.ico`.
- `Start-Repo52.ps1` now opens the dashboard with a fresh cache-busting URL.
- Login screen now says `Quantum Command 52`.
- Login screen has an `Open local demo` button.
- Dashboard starts on the Grants/resource ledger.
- Source links are visible text buttons: `Open source`.
- Demo grants, housing, and catalog rows use real source URLs.
- Housing and inventory records now store `source_url`.
- Generated Markdown reports include clickable source links.

## Important Files

- `web-dashboard/src/main.jsx`: main React app cleanup.
- `web-dashboard/src/styles.css`: layout and visible source-link button styles.
- `web-dashboard/server.py`: demo seed rows, source URL fields, paper-capital cleanup.
- `data/grants.csv`: real starter grant/resource rows.
- `data/housing_violations.csv`: real housing/help resource rows.
- `data/shell_items.csv`: real comparable-source starter rows.
- `grants.py`: clickable official-source links in generated output.
- `housing_violations.py`: clickable source links in generated output.
- `shell_catalog.py`: Markdown estimate output with clickable comparable-source links.
- `strict_macro_quantum_v10.py`: default bankroll changed from `500000` to `1000`.
- `web-dashboard/openapi.json`: public API contract no longer advertises Stripe checkout.
- `web-dashboard/alembic/versions/002_add_grant_source_url.py`: grant source URL migration.
- `web-dashboard/alembic/versions/003_add_source_urls_to_housing_inventory.py`: housing/catalog source URL migration.

## Restore Notes

Before these changes are committed, individual files can be restored with Git, for example:

```powershell
git restore -- web-dashboard/src/main.jsx
```

After these changes are committed and pushed, use GitHub history or `git log` to find the previous commit and restore only the file or section needed.

The local demo database is ignored at:

```text
web-dashboard/data.db
```

Deleting that ignored file resets the local demo data on the next launcher start.
