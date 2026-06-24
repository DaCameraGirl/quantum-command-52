<p align="center">
  <img src="docs/assets/readme-hero.svg" alt="Quantum Command 52 — 带资源台账的 IBM/Qiskit 实验室" width="100%"/>
</p>

# Quantum Command 52

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/🇺🇸_English-132033?style=for-the-badge&labelColor=070b12" alt="English"/></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/🇪🇸_Español-132033?style=for-the-badge&labelColor=070b12" alt="Español"/></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/🇫🇷_Français-132033?style=for-the-badge&labelColor=070b12" alt="Français"/></a>
  <a href="README.de.md"><img src="https://img.shields.io/badge/🇩🇪_Deutsch-132033?style=for-the-badge&labelColor=070b12" alt="Deutsch"/></a>
  <a href="README.pt-BR.md"><img src="https://img.shields.io/badge/🇧🇷_Português-132033?style=for-the-badge&labelColor=070b12" alt="Português"/></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/🇨🇳_中文-38bdf8?style=for-the-badge&labelColor=070b12" alt="中文"/></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/🇯🇵_日本語-132033?style=for-the-badge&labelColor=070b12" alt="日本語"/></a>
  <a href="README.ko.md"><img src="https://img.shields.io/badge/🇰🇷_한국어-132033?style=for-the-badge&labelColor=070b12" alt="한국어"/></a>
  <a href="README.it.md"><img src="https://img.shields.io/badge/🇮🇹_Italiano-132033?style=for-the-badge&labelColor=070b12" alt="Italiano"/></a>
  <a href="README.ar.md"><img src="https://img.shields.io/badge/🇸🇦_العربية-132033?style=for-the-badge&labelColor=070b12" alt="العربية"/></a>
</p>

<p align="center">
  <a href="https://dacameragirl.github.io/quantum-command-52/"><img src="https://img.shields.io/badge/🌐_在线演示-38bdf8?style=for-the-badge&labelColor=070b12" alt="在线演示"/></a>
  <a href="https://dacameragirl.github.io/links/"><img src="https://img.shields.io/badge/🔗_项目中心-132033?style=for-the-badge&labelColor=070b12" alt="项目中心"/></a>
  <img src="https://img.shields.io/badge/Qiskit-IBM-6929C4?style=for-the-badge&logo=qiskit&logoColor=white" alt="Qiskit"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=070b12" alt="Python"/>
  <img src="https://img.shields.io/badge/React-149ECA?style=for-the-badge&logo=react&logoColor=white&labelColor=070b12" alt="React"/>
  <img src="https://img.shields.io/badge/Pages_demo-38bdf8?style=for-the-badge&labelColor=070b12" alt="Pages demo"/>
</p>

<p align="center">
  <img src="docs/assets/quantum-circuit.svg" alt="动画量子电路 — 量子比特、门、纠缠" width="620"/>
</p>

**本地优先的 IBM/Qiskit 量子实验室，附带实用的资源台账。**

它**不是** Stripe 结账应用，不是房地产演示，也不承诺金钱、福利、住房或法律结果有保障。它帮助在一个地方整理真实链接、真实笔记和量子实验。

<p align="center">
  <img src="docs/assets/readme-status.svg" alt="本地优先量子实验室 — 非计费，非保证结果" width="100%"/>
</p>

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## 仓库 vs. 在线演示

| 内容 | URL |
|---|---|
| **在线演示**（GitHub Pages，静态） | [dacameragirl.github.io/quantum-command-52](https://dacameragirl.github.io/quantum-command-52/) |
| **GitHub 仓库** | [github.com/DaCameraGirl/quantum-command-52](https://github.com/DaCameraGirl/quantum-command-52) |
| **完整仪表板**（本地 API + Vite） | 桌面快捷方式 **52** → `Start-Repo52.ps1` |
| **项目中心** | [dacameragirl.github.io/links](https://dacameragirl.github.io/links/) |

最新清理说明：[CHANGELOG_REPO52_CLEANUP.md](CHANGELOG_REPO52_CLEANUP.md)

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## 用途

| 领域 | 功能 |
|---|---|
| **Quantum** | 运行和检查 IBM/Qiskit 实验；QAOA、QML、模拟投资组合研究 |
| **Grants** | 对补助、奖学金、紧急援助和福利线索进行排序 |
| **Housing** | 跟踪庇护所、法律援助、咨询、211 和住房证据 |
| **Catalog** | 物品/价值研究，附带可比较来源链接 |
| **Links** | 保持官方 `source_url` 列可点击 — 不埋在备注中 |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## 快速开始

在 PowerShell 中从仓库根目录运行：

```powershell
python grants.py rank
python housing_violations.py summarize
python shell_catalog.py estimate
python quantum_portfolio.py --capital 1000
python qml_signal_engine.py --capital 1000
python strict_macro_quantum_v10.py --preflight
```

输出保存在 `output` 文件夹中。

## 桌面快捷方式

名为 **52** 的桌面快捷方式通过 `Start-Repo52.ps1` 启动本地仪表板。

| 界面 | URL |
|---|---|
| 后端 API | http://127.0.0.1:8787 |
| 前端仪表板 | http://127.0.0.1:5173 |
| 图标 | `assets/repo52-52.ico` |

## 仪表板标签页

| 标签页 | 内容 |
|---|---|
| **Grants** | 官方援助、奖学金、紧急资源和福利链接 |
| **Housing** | 庇护所、法律援助、咨询、211、住房证据跟踪 |
| **Catalog** | 物品/价值研究，附带可比较来源链接 |
| **Quantum** | IBM/Qiskit 和本地模拟研究工具 |

**已从可见应用中移除：** 计费/Stripe 结账 · 房地产 Deals 演示 · 虚假的 `$500,000` 指挥资本用语

## 主要文件

| 文件 | 作用 |
|---|---|
| `grants.py` | 从 `data/grants.csv` 对补助和帮助资源线索排序 |
| `housing_violations.py` | 从 `data/housing_violations.csv` 生成住房/帮助摘要 |
| `shell_catalog.py` | 从 `data/shell_items.csv` 估算目录价值 |
| `quantum_portfolio.py` | 本地量子启发式模拟投资组合优化器 |
| `qml_signal_engine.py` | 本地 QML 形态模拟信号引擎 |
| `strict_macro_quantum_v10.py` | 严格的 IBM/Qiskit/yfinance/Torch 流水线 |
| `web-dashboard/` | React 仪表板 + Python API 服务器 |
| `IBM_QUANTUM_TOKEN_GUIDE.md` | IBM Quantum 令牌设置 |
| `PROJECT_LOG.md` | 项目历史 |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## IBM Quantum

严格 V10 脚本需要企业依赖和 IBM Runtime 访问权限。

```powershell
py -3.11 strict_macro_quantum_v10.py --preflight
```

将密钥保存在 `.env` 中。不要提交 IBM、Alpaca、数据库或其他私钥。

### Alpaca 模拟研究

实盘交易被有意阻止。仅模拟预览/提交：

```powershell
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders
py -3.11 strict_macro_quantum_v10.py --bankroll 1000 --preview-alpaca-orders --submit-paper-orders
```

## Web 仪表板设置

```powershell
cd web-dashboard
npm install
py -3.11 -m pip install -r requirements.txt
py -3.11 server.py
```

第二个终端：

```powershell
cd web-dashboard
npm run dev
```

打开 http://127.0.0.1:5173

## 本地演示模式

快捷方式以后台方式启动：

```text
REPO52_DEMO_MODE=true
APP_ENV=development
REQUIRE_ALEMBIC_MIGRATIONS=false
```

使用被忽略的本地数据库：`web-dashboard/data.db` — 删除以重置演示行。

## 生产数据库

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

| 服务 | URL / 作用 |
|---|---|
| 应用 + API | http://127.0.0.1:8080 |
| PostgreSQL | 内部 Docker 网络，`postgres_data` 卷 |
| 迁移任务 | `alembic upgrade head` |

<p align="center">
  <img src="docs/assets/readme-divider.svg" alt="" width="100%"/>
</p>

## 实际使用

1. 打开 `data` 中的 CSV 文件。
2. 添加真实机会、资源、证据或物品。
3. 在 `source_url` 列中保留官方 URL。
4. 运行匹配的脚本。
5. 使用 `output` 中生成的 Markdown/CSV。

## 限制

- 任何脚本都不保证补助、福利、和解或售价。
- 任何脚本都不是法律或财务建议。
- 不要上传来自陌生人或随机网站的私人文件。
- 住房/法律摘要仅为整理工具 — 采取行动请咨询合格的法律援助。

## 贡献者

- **Angela Hudson** ([DaCameraGirl](https://github.com/DaCameraGirl)) — 产品方向、资源数据、测试
- **Claude** — 仪表板清理、Pages 部署、量子脚本

## 许可证

Copyright (c) 2026 Angela Nelson. 保留所有权利。

仅供查看公开。未经事先书面许可，不得使用、复制、修改、发布、分发、出售、再许可或创建衍生作品。

完整条款：[LICENSE](LICENSE)