<p align="center">
  <img src="docs/assets/readme-hero.svg" alt="Quantum Command 52 — リソース台帳付き IBM/Qiskit ラボ" width="100%"/>
</p>

# Quantum Command 52

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/🇺🇸_English-132033?style=for-the-badge&labelColor=070b12" alt="English"/></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/🇪🇸_Español-132033?style=for-the-badge&labelColor=070b12" alt="Español"/></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/🇫🇷_Français-132033?style=for-the-badge&labelColor=070b12" alt="Français"/></a>
  <a href="README.de.md"><img src="https://img.shields.io/badge/🇩🇪_Deutsch-132033?style=for-the-badge&labelColor=070b12" alt="Deutsch"/></a>
  <a href="README.pt-BR.md"><img src="https://img.shields.io/badge/🇧🇷_Português-132033?style=for-the-badge&labelColor=070b12" alt="Português"/></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/🇨🇳_中文-132033?style=for-the-badge&labelColor=070b12" alt="中文"/></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/🇯🇵_日本語-38bdf8?style=for-the-badge&labelColor=070b12" alt="日本語"/></a>
  <a href="README.ko.md"><img src="https://img.shields.io/badge/🇰🇷_한국어-132033?style=for-the-badge&labelColor=070b12" alt="한국어"/></a>
  <a href="README.it.md"><img src="https://img.shields.io/badge/🇮🇹_Italiano-132033?style=for-the-badge&labelColor=070b12" alt="Italiano"/></a>
  <a href="README.ar.md"><img src="https://img.shields.io/badge/🇸🇦_العربية-132033?style=for-the-badge&labelColor=070b12" alt="العربية"/></a>
</p>

<p align="center">
  <a href="https://dacameragirl.github.io/quantum-command-52/"><img src="https://img.shields.io/badge/🌐_ライブデモ-38bdf8?style=for-the-badge&labelColor=070b12" alt="ライブデモ"/></a>
  <a href="https://dacameragirl.github.io/links/"><img src="https://img.shields.io/badge/🔗_プロジェクトハブ-132033?style=for-the-badge&labelColor=070b12" alt="プロジェクトハブ"/></a>
  <img src="https://img.shields.io/badge/Qiskit-IBM-6929C4?style=for-the-badge&logo=qiskit&logoColor=white" alt="Qiskit"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=070b12" alt="Python"/>
  <img src="https://img.shields.io/badge/React-149ECA?style=for-the-badge&logo=react&logoColor=white&labelColor=070b12" alt="React"/>
  <img src="https://img.shields.io/badge/Pages_demo-38bdf8?style=for-the-badge&labelColor=070b12" alt="Pages demo"/>
</p>

<p align="center">
  <img src="docs/assets/quantum-circuit.svg" alt="アニメーション量子回路 — 量子ビット、ゲート、もつれ" width="620"/>
</p>

**実用的なリソース台帳を備えたローカルファーストの IBM/Qiskit 量子ラボ。**

Stripe 決済アプリでも、不動産デモでもなく、お金・給付・住宅・法的結果が保証されるという約束でも**ありません**。実際のリンク、実際のメモ、量子実験を一か所に整理するのに役立ちます。

<p align="center">
  <img src="docs/assets/readme-status.svg" alt="ローカルファースト量子ラボ — 課金なし、結果保証なし" width="100%"/>
</p>

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## リポジトリ vs. ライブデモ

| 内容 | URL |
|---|---|
| **ライブデモ**（GitHub Pages、静的） | [dacameragirl.github.io/quantum-command-52](https://dacameragirl.github.io/quantum-command-52/) |
| **GitHub リポジトリ** | [github.com/DaCameraGirl/quantum-command-52](https://github.com/DaCameraGirl/quantum-command-52) |
| **フルダッシュボード**（ローカル API + Vite） | デスクトップショートカット **52** → `Start-Repo52.ps1` |
| **プロジェクトハブ** | [dacameragirl.github.io/links](https://dacameragirl.github.io/links/) |

最新のクリーンアップメモ：[CHANGELOG_REPO52_CLEANUP.md](CHANGELOG_REPO52_CLEANUP.md)

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## 用途

| 領域 | 機能 |
|---|---|
| **Quantum** | IBM/Qiskit 実験の実行と検査；QAOA、QML、ペーパーポートフォリオ研究 |
| **Grants** | 助成金、奨学金、緊急援助、給付のリードをランク付け |
| **Housing** | シェルター、法的支援、カウンセリング、211、住宅証拠の追跡 |
| **Catalog** | 比較可能なソースリンク付きの品目/価値調査 |
| **Links** | 公式 `source_url` 列をクリック可能に維持 — メモに埋め込まない |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## クイックスタート

PowerShell でリポジトリのルートから：

```powershell
python grants.py rank
python housing_violations.py summarize
python shell_catalog.py estimate
python quantum_portfolio.py --capital 1000
python qml_signal_engine.py --capital 1000
python strict_macro_quantum_v10.py --preflight
```

出力は `output` フォルダに保存されます。

## デスクトップショートカット

**52** という名前のデスクトップショートカットは `Start-Repo52.ps1` 経由でローカルダッシュボードを起動します。

| 画面 | URL |
|---|---|
| バックエンド API | http://127.0.0.1:8787 |
| フロントエンドダッシュボード | http://127.0.0.1:5173 |
| アイコン | `assets/repo52-52.ico` |

## ダッシュボードタブ

| タブ | 内容 |
|---|---|
| **Grants** | 公式の援助、奨学金、緊急リソース、給付リンク |
| **Housing** | シェルター、法的支援、カウンセリング、211、住宅証拠の追跡 |
| **Catalog** | 比較可能なソースリンク付きの品目/価値調査 |
| **Quantum** | IBM/Qiskit とローカルペーパー研究ツール |

**表示アプリから削除：** 課金/Stripe チェックアウト · 不動産 Deals デモ · 偽の `$500,000` コマンド資本表現

## 主要ファイル

| ファイル | 役割 |
|---|---|
| `grants.py` | `data/grants.csv` から助成金と支援リソースのリードをランク付け |
| `housing_violations.py` | `data/housing_violations.csv` から住宅/支援の要約 |
| `shell_catalog.py` | `data/shell_items.csv` からカタログ価値の推定 |
| `quantum_portfolio.py` | ローカル量子インスパイア型ペーパーポートフォリオ最適化 |
| `qml_signal_engine.py` | ローカル QML 形式ペーパーシグナルエンジン |
| `strict_macro_quantum_v10.py` | 厳格な IBM/Qiskit/yfinance/Torch パイプライン |
| `web-dashboard/` | React ダッシュボード + Python API サーバー |
| `IBM_QUANTUM_TOKEN_GUIDE.md` | IBM Quantum トークン設定 |
| `PROJECT_LOG.md` | プロジェクト履歴 |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## IBM Quantum

厳格な V10 スクリプトはエンタープライズ依存関係と IBM Runtime アクセスを必要とします。

```powershell
py -3.11 strict_macro_quantum_v10.py --preflight
```

シークレットは `.env` に保管してください。IBM、Alpaca、データベース、その他の秘密鍵はコミットしないでください。

### Alpaca ペーパー研究

ライブ取引は意図的にブロックされています。ペーパーのプレビュー/送信のみ：

```powershell
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders --submit-paper-orders
```

## Web ダッシュボードのセットアップ

```powershell
cd web-dashboard
npm install
py -3.11 -m pip install -r requirements.txt
py -3.11 server.py
```

2 つ目のターミナル：

```powershell
cd web-dashboard
npm run dev
```

http://127.0.0.1:5173 を開く

## ローカルデモモード

ショートカットは次の設定でバックエンドを起動します：

```text
REPO52_DEMO_MODE=true
APP_ENV=development
REQUIRE_ALEMBIC_MIGRATIONS=false
```

無視されるローカル DB を使用：`web-dashboard/data.db` — 削除するとデモ行をリセット

## 本番データベース

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

| サービス | URL / 役割 |
|---|---|
| アプリ + API | http://127.0.0.1:8080 |
| PostgreSQL | 内部 Docker ネットワーク、`postgres_data` ボリューム |
| マイグレーションジョブ | `alembic upgrade head` |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## 実際に使う

1. `data` 内の CSV ファイルを開く。
2. 実際の機会、リソース、証拠、品目を追加する。
3. `source_url` 列に公式 URL を保持する。
4. 対応するスクリプトを実行する。
5. `output` で生成された Markdown/CSV を使用する。

## 制限事項

- いかなるスクリプトも助成金、給付、和解、販売価格を保証しません。
- いかなるスクリプトも法的または財務的助言ではありません。
- 見知らぬ人やランダムなウェブサイトからの私的書類をアップロードしないでください。
- 住宅/法的要約は整理ツールです — 行動については資格のある法的支援に相談してください。

## コントリビューター

- **Angela Hudson** ([DaCameraGirl](https://github.com/DaCameraGirl)) — プロダクト方向性、リソースデータ、テスト
- **Claude** — ダッシュボードのクリーンアップ、Pages デプロイ、量子スクリプト

## ライセンス

Copyright (c) 2026 Angela Nelson. All Rights Reserved.

閲覧のみ公開。事前の書面による許可なく、使用、複製、変更、公開、配布、販売、サブライセンス、または派生作品の作成は禁止されています。

完全な条項：[LICENSE](LICENSE)