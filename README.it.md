<p align="center">
  <img src="docs/assets/readme-hero.svg" alt="Quantum Command 52 — laboratorio IBM/Qiskit con registri delle risorse" width="100%"/>
</p>

# Quantum Command 52

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/🇺🇸_English-132033?style=for-the-badge&labelColor=070b12" alt="English"/></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/🇪🇸_Español-132033?style=for-the-badge&labelColor=070b12" alt="Español"/></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/🇫🇷_Français-132033?style=for-the-badge&labelColor=070b12" alt="Français"/></a>
  <a href="README.de.md"><img src="https://img.shields.io/badge/🇩🇪_Deutsch-132033?style=for-the-badge&labelColor=070b12" alt="Deutsch"/></a>
  <a href="README.pt-BR.md"><img src="https://img.shields.io/badge/🇧🇷_Português-132033?style=for-the-badge&labelColor=070b12" alt="Português"/></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/🇨🇳_中文-132033?style=for-the-badge&labelColor=070b12" alt="中文"/></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/🇯🇵_日本語-132033?style=for-the-badge&labelColor=070b12" alt="日本語"/></a>
  <a href="README.ko.md"><img src="https://img.shields.io/badge/🇰🇷_한국어-132033?style=for-the-badge&labelColor=070b12" alt="한국어"/></a>
  <a href="README.it.md"><img src="https://img.shields.io/badge/🇮🇹_Italiano-38bdf8?style=for-the-badge&labelColor=070b12" alt="Italiano"/></a>
  <a href="README.ar.md"><img src="https://img.shields.io/badge/🇸🇦_العربية-132033?style=for-the-badge&labelColor=070b12" alt="العربية"/></a>
</p>

<p align="center">
  <a href="https://dacameragirl.github.io/quantum-command-52/"><img src="https://img.shields.io/badge/🌐_Demo_live-38bdf8?style=for-the-badge&labelColor=070b12" alt="Demo live"/></a>
  <a href="https://dacameragirl.github.io/links/"><img src="https://img.shields.io/badge/🔗_Hub_progetti-132033?style=for-the-badge&labelColor=070b12" alt="Hub progetti"/></a>
  <img src="https://img.shields.io/badge/Qiskit-IBM-6929C4?style=for-the-badge&logo=qiskit&logoColor=white" alt="Qiskit"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=070b12" alt="Python"/>
  <img src="https://img.shields.io/badge/React-149ECA?style=for-the-badge&logo=react&logoColor=white&labelColor=070b12" alt="React"/>
  <img src="https://img.shields.io/badge/Pages_demo-38bdf8?style=for-the-badge&labelColor=070b12" alt="Pages demo"/>
</p>

<p align="center">
  <img src="docs/assets/quantum-circuit.svg" alt="Circuito quantistico animato — qubit, gate, entanglement" width="620"/>
</p>

**Laboratorio quantistico IBM/Qiskit local-first con registri pratici delle risorse integrati.**

**Non** è un'app di checkout Stripe, non è una demo immobiliare e non promette che denaro, benefici, alloggio o esiti legali siano garantiti. Aiuta a organizzare link reali, note reali ed esperimenti quantistici in un unico posto.

<p align="center">
  <img src="docs/assets/readme-status.svg" alt="Laboratorio quantistico local-first — niente fatturazione, niente esiti garantiti" width="100%"/>
</p>

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## Repository vs. demo live

| Cosa | URL |
|---|---|
| **Demo live** (GitHub Pages, statico) | [dacameragirl.github.io/quantum-command-52](https://dacameragirl.github.io/quantum-command-52/) |
| **Repository GitHub** | [github.com/DaCameraGirl/quantum-command-52](https://github.com/DaCameraGirl/quantum-command-52) |
| **Dashboard completa** (API locale + Vite) | Scorciatoia desktop **52** → `Start-Repo52.ps1` |
| **Hub progetti** | [dacameragirl.github.io/links](https://dacameragirl.github.io/links/) |

Ultime note di pulizia: [CHANGELOG_REPO52_CLEANUP.md](CHANGELOG_REPO52_CLEANUP.md)

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## A cosa serve

| Area | Funzione |
|---|---|
| **Quantum** | Eseguire e ispezionare esperimenti IBM/Qiskit; QAOA, QML, ricerca portafoglio paper |
| **Grants** | Classificare lead di sovvenzioni, borse di studio, aiuti di emergenza e benefici |
| **Housing** | Tracciare rifugi, assistenza legale, consulenza, 211 e prove abitative |
| **Catalog** | Ricerca articoli/valore con link a fonti comparabili |
| **Links** | Mantenere le colonne `source_url` ufficiali cliccabili — non sepolte nelle note |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## Avvio rapido

Dalla root del repository in PowerShell:

```powershell
python grants.py rank
python housing_violations.py summarize
python shell_catalog.py estimate
python quantum_portfolio.py --capital 1000
python qml_signal_engine.py --capital 1000
python strict_macro_quantum_v10.py --preflight
```

Gli output finiscono nella cartella `output`.

## Scorciatoia desktop

La scorciatoia desktop chiamata **52** avvia la dashboard locale tramite `Start-Repo52.ps1`.

| Superficie | URL |
|---|---|
| API backend | http://127.0.0.1:8787 |
| Dashboard frontend | http://127.0.0.1:5173 |
| Icona | `assets/repo52-52.ico` |

## Tab della dashboard

| Tab | Contenuto |
|---|---|
| **Grants** | Link ufficiali di aiuto, borse di studio, risorse di emergenza e benefici |
| **Housing** | Rifugi, assistenza legale, consulenza, 211, tracciamento prove abitative |
| **Catalog** | Ricerca articoli/valore con link a fonti comparabili |
| **Quantum** | Strumenti IBM/Qiskit e ricerca locale su carta |

**Rimosso dall'app visibile:** Fatturazione/Stripe checkout · Demo immobiliare Deals · Linguaggio falso di capitale di comando `$500,000`

## File principali

| File | Ruolo |
|---|---|
| `grants.py` | Classifica lead di sovvenzioni e risorse di aiuto da `data/grants.csv` |
| `housing_violations.py` | Riepilogo alloggio/aiuto da `data/housing_violations.csv` |
| `shell_catalog.py` | Stime di valore del catalogo da `data/shell_items.csv` |
| `quantum_portfolio.py` | Ottimizzatore locale di portafoglio paper ispirato al quantistico |
| `qml_signal_engine.py` | Motore locale di segnali paper in formato QML |
| `strict_macro_quantum_v10.py` | Pipeline rigorosa IBM/Qiskit/yfinance/Torch |
| `web-dashboard/` | Dashboard React + server API Python |
| `IBM_QUANTUM_TOKEN_GUIDE.md` | Configurazione token IBM Quantum |
| `PROJECT_LOG.md` | Cronologia del progetto |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## IBM Quantum

Lo script rigoroso V10 richiede dipendenze enterprise e accesso a IBM Runtime.

```powershell
py -3.11 strict_macro_quantum_v10.py --preflight
```

Conserva i segreti in `.env`. Non committare chiavi private IBM, Alpaca, database o altre.

### Ricerca paper Alpaca

Il trading live è intenzionalmente bloccato. Solo anteprima/invio paper:

```powershell
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders --submit-paper-orders
```

## Configurazione dashboard web

```powershell
cd web-dashboard
npm install
py -3.11 -m pip install -r requirements.txt
py -3.11 server.py
```

Secondo terminale:

```powershell
cd web-dashboard
npm run dev
```

Apri http://127.0.0.1:5173

## Modalità demo locale

La scorciatoia avvia il backend con:

```text
REPO52_DEMO_MODE=true
APP_ENV=development
REQUIRE_ALEMBIC_MIGRATIONS=false
```

Usa DB locale ignorato: `web-dashboard/data.db` — elimina per reimpostare le righe demo.

## Database di produzione

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

| Servizio | URL / ruolo |
|---|---|
| App + API | http://127.0.0.1:8080 |
| PostgreSQL | Rete Docker interna, volume `postgres_data` |
| Job di migrazione | `alembic upgrade head` |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## Usalo davvero

1. Apri i file CSV in `data`.
2. Aggiungi opportunità, risorse, prove o articoli reali.
3. Mantieni gli URL ufficiali nelle colonne `source_url`.
4. Esegui lo script corrispondente.
5. Usa il Markdown/CSV generato in `output`.

## Limiti

- Nessuno script garantisce una sovvenzione, beneficio, accordo o prezzo di vendita.
- Nessuno script è consulenza legale o finanziaria.
- Non caricare documenti privati da sconosciuti o siti web casuali.
- I riepiloghi abitativi/legali sono organizzatori — consulta assistenza legale qualificata per agire.

## Collaboratori

- **Angela Hudson** ([DaCameraGirl](https://github.com/DaCameraGirl)) — direzione prodotto, dati sulle risorse, test
- **Claude** — pulizia dashboard, deploy Pages, script quantistici

## Licenza

Copyright (c) 2026 Angela Nelson. Tutti i diritti riservati.

Pubblico solo per la visualizzazione. Nessun permesso di usare, copiare, modificare, pubblicare, distribuire, vendere, sublicenziare o creare opere derivate senza autorizzazione scritta preventiva.

Termini completi: [LICENSE](LICENSE)