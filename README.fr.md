<p align="center">
  <img src="docs/assets/readme-hero.svg" alt="Quantum Command 52 — laboratoire IBM/Qiskit avec registres de ressources" width="100%"/>
</p>

# Quantum Command 52

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/🇺🇸_English-132033?style=for-the-badge&labelColor=070b12" alt="English"/></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/🇪🇸_Español-132033?style=for-the-badge&labelColor=070b12" alt="Español"/></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/🇫🇷_Français-38bdf8?style=for-the-badge&labelColor=070b12" alt="Français"/></a>
  <a href="README.de.md"><img src="https://img.shields.io/badge/🇩🇪_Deutsch-132033?style=for-the-badge&labelColor=070b12" alt="Deutsch"/></a>
  <a href="README.pt-BR.md"><img src="https://img.shields.io/badge/🇧🇷_Português-132033?style=for-the-badge&labelColor=070b12" alt="Português"/></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/🇨🇳_中文-132033?style=for-the-badge&labelColor=070b12" alt="中文"/></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/🇯🇵_日本語-132033?style=for-the-badge&labelColor=070b12" alt="日本語"/></a>
  <a href="README.ko.md"><img src="https://img.shields.io/badge/🇰🇷_한국어-132033?style=for-the-badge&labelColor=070b12" alt="한국어"/></a>
  <a href="README.it.md"><img src="https://img.shields.io/badge/🇮🇹_Italiano-132033?style=for-the-badge&labelColor=070b12" alt="Italiano"/></a>
  <a href="README.ar.md"><img src="https://img.shields.io/badge/🇸🇦_العربية-132033?style=for-the-badge&labelColor=070b12" alt="العربية"/></a>
</p>

<p align="center">
  <a href="https://dacameragirl.github.io/quantum-command-52/"><img src="https://img.shields.io/badge/🌐_Démo_en_ligne-38bdf8?style=for-the-badge&labelColor=070b12" alt="Démo en ligne"/></a>
  <a href="https://dacameragirl.github.io/links/"><img src="https://img.shields.io/badge/🔗_Hub_projets-132033?style=for-the-badge&labelColor=070b12" alt="Hub projets"/></a>
  <img src="https://img.shields.io/badge/Qiskit-IBM-6929C4?style=for-the-badge&logo=qiskit&logoColor=white" alt="Qiskit"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=070b12" alt="Python"/>
  <img src="https://img.shields.io/badge/React-149ECA?style=for-the-badge&logo=react&logoColor=white&labelColor=070b12" alt="React"/>
  <img src="https://img.shields.io/badge/Pages_demo-38bdf8?style=for-the-badge&labelColor=070b12" alt="Pages demo"/>
</p>

<p align="center">
  <img src="docs/assets/quantum-circuit.svg" alt="Circuit quantique animé — qubits, portes, intrication" width="620"/>
</p>

**Laboratoire quantique IBM/Qiskit local-first avec des registres de ressources pratiques intégrés.**

Ce n'**est pas** une application de paiement Stripe, pas une démo immobilière, et pas une promesse que l'argent, les prestations, le logement ou les résultats juridiques sont garantis. Il aide à organiser de vrais liens, de vraies notes et des expériences quantiques au même endroit.

<p align="center">
  <img src="docs/assets/readme-status.svg" alt="Laboratoire quantique local-first — pas de facturation, pas de résultats garantis" width="100%"/>
</p>

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## Dépôt vs. démo en ligne

| Quoi | URL |
|---|---|
| **Démo en ligne** (GitHub Pages, statique) | [dacameragirl.github.io/quantum-command-52](https://dacameragirl.github.io/quantum-command-52/) |
| **Dépôt GitHub** | [github.com/DaCameraGirl/quantum-command-52](https://github.com/DaCameraGirl/quantum-command-52) |
| **Tableau de bord complet** (API locale + Vite) | Raccourci bureau **52** → `Start-Repo52.ps1` |
| **Hub de projets** | [dacameragirl.github.io/links](https://dacameragirl.github.io/links/) |

Dernières notes de nettoyage : [CHANGELOG_REPO52_CLEANUP.md](CHANGELOG_REPO52_CLEANUP.md)

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## À quoi ça sert

| Domaine | Fonction |
|---|---|
| **Quantum** | Exécuter et inspecter des expériences IBM/Qiskit ; QAOA, QML, recherche de portefeuille papier |
| **Grants** | Classer les pistes de subventions, bourses, aides d'urgence et prestations |
| **Housing** | Suivre refuges, aide juridique, conseil, 211 et preuves de logement |
| **Catalog** | Recherche articles/valeur avec liens vers des sources comparables |
| **Links** | Garder les colonnes `source_url` officielles cliquables — pas enfouies dans les notes |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## Démarrage rapide

Depuis la racine du dépôt dans PowerShell :

```powershell
python grants.py rank
python housing_violations.py summarize
python shell_catalog.py estimate
python quantum_portfolio.py --capital 1000
python qml_signal_engine.py --capital 1000
python strict_macro_quantum_v10.py --preflight
```

Les sorties sont enregistrées dans le dossier `output`.

## Raccourci bureau

Le raccourci bureau nommé **52** lance le tableau de bord local via `Start-Repo52.ps1`.

| Surface | URL |
|---|---|
| API backend | http://127.0.0.1:8787 |
| Tableau de bord frontend | http://127.0.0.1:5173 |
| Icône | `assets/repo52-52.ico` |

## Onglets du tableau de bord

| Onglet | Contenu |
|---|---|
| **Grants** | Liens officiels d'aide, bourses, ressources d'urgence et prestations |
| **Housing** | Refuges, aide juridique, conseil, 211, suivi des preuves de logement |
| **Catalog** | Recherche articles/valeur avec liens vers des sources comparables |
| **Quantum** | Outils IBM/Qiskit et recherche locale sur papier |

**Retiré de l'app visible :** Facturation/Stripe checkout · Démo immobilière Deals · Langage fictif de capital de commande `$500,000`

## Fichiers principaux

| Fichier | Rôle |
|---|---|
| `grants.py` | Classe les pistes de subventions et ressources d'aide depuis `data/grants.csv` |
| `housing_violations.py` | Résumé logement/aide depuis `data/housing_violations.csv` |
| `shell_catalog.py` | Estimations de valeur du catalogue depuis `data/shell_items.csv` |
| `quantum_portfolio.py` | Optimiseur local de portefeuille papier inspiré du quantique |
| `qml_signal_engine.py` | Moteur local de signaux papier de type QML |
| `strict_macro_quantum_v10.py` | Pipeline strict IBM/Qiskit/yfinance/Torch |
| `web-dashboard/` | Tableau de bord React + serveur API Python |
| `IBM_QUANTUM_TOKEN_GUIDE.md` | Configuration du jeton IBM Quantum |
| `PROJECT_LOG.md` | Historique du projet |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## IBM Quantum

Le script strict V10 nécessite des dépendances entreprise et l'accès IBM Runtime.

```powershell
py -3.11 strict_macro_quantum_v10.py --preflight
```

Conservez les secrets dans `.env`. Ne commitez pas les clés privées IBM, Alpaca, base de données ou autres.

### Recherche papier Alpaca

Le trading en direct est volontairement bloqué. Aperçu/soumission papier uniquement :

```powershell
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders --submit-paper-orders
```

## Configuration du tableau de bord web

```powershell
cd web-dashboard
npm install
py -3.11 -m pip install -r requirements.txt
py -3.11 server.py
```

Deuxième terminal :

```powershell
cd web-dashboard
npm run dev
```

Ouvrez http://127.0.0.1:5173

## Mode démo local

Le raccourci démarre le backend avec :

```text
REPO52_DEMO_MODE=true
APP_ENV=development
REQUIRE_ALEMBIC_MIGRATIONS=false
```

Utilise une BD locale ignorée : `web-dashboard/data.db` — supprimez pour réinitialiser les lignes de démo.

## Base de données de production

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

| Service | URL / rôle |
|---|---|
| App + API | http://127.0.0.1:8080 |
| PostgreSQL | Réseau Docker interne, volume `postgres_data` |
| Tâche de migration | `alembic upgrade head` |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## Utilisation réelle

1. Ouvrez les fichiers CSV dans `data`.
2. Ajoutez de vraies opportunités, ressources, preuves ou articles.
3. Conservez les URL officielles dans les colonnes `source_url`.
4. Exécutez le script correspondant.
5. Utilisez le Markdown/CSV généré dans `output`.

## Limites

- Aucun script ne garantit une subvention, prestation, règlement ou prix de vente.
- Aucun script ne constitue un conseil juridique ou financier.
- Ne téléversez pas de documents privés provenant d'inconnus ou de sites aléatoires.
- Les résumés logement/juridique sont des organisateurs — consultez une aide juridique qualifiée pour agir.

## Contributeurs

- **Angela Hudson** ([DaCameraGirl](https://github.com/DaCameraGirl)) — direction produit, données de ressources, tests
- **Claude** — nettoyage du tableau de bord, déploiement Pages, scripts quantiques

## Licence

Copyright (c) 2026 Angela Nelson. Tous droits réservés.

Public en consultation uniquement. Aucune autorisation d'utiliser, copier, modifier, publier, distribuer, vendre, sous-licencier ou créer des œuvres dérivées sans autorisation écrite préalable.

Conditions complètes : [LICENSE](LICENSE)