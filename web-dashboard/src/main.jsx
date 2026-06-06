import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Boxes,
  CheckCircle2,
  CircuitBoard,
  Database,
  FileSearch,
  Gauge,
  Gem,
  GraduationCap,
  Home,
  Landmark,
  Lock,
  LogOut,
  PieChart,
  ShieldCheck,
  UserPlus,
  Zap,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart as RePieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./styles.css";

const COLORS = ["#38bdf8", "#22c55e", "#f97316", "#a78bfa", "#f43f5e", "#facc15"];
const COMMAND_CAPITAL = 500000;

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Request failed");
  return payload;
}

function AuthPanel({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [displayName, setDisplayName] = useState("Angela");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const payload = await api(`/api/${mode}`, {
        method: "POST",
        body: JSON.stringify({ displayName, email, password }),
      });
      onAuth(payload.user);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-aside">
        <div className="brand-mark">
          <CircuitBoard size={24} />
        </div>
        <p className="eyebrow">Data-Analytics command access</p>
        <h1>Macro Asset Command Center</h1>
        <p className="auth-copy">
          Secure entry for portfolio telemetry, quantum model outputs, and practical intelligence tools.
        </p>
        <div className="security-grid">
          <div className="security-row">
            <ShieldCheck size={18} />
            <span>JWT authorization</span>
          </div>
          <div className="security-row">
            <Lock size={18} />
            <span>PostgreSQL identity layer</span>
          </div>
        </div>
      </section>

      <section className="auth-panel" aria-label="Authentication form">
        <div className="segmented">
          <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">
            <Lock size={16} /> Sign in
          </button>
          <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")} type="button">
            <UserPlus size={16} /> Register
          </button>
        </div>
        <form onSubmit={submit}>
          {mode === "register" && (
            <label>
              Display name
              <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
          )}
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" />
          </label>
          <label>
            Password
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
          </label>
          {error && <div className="error-line">{error}</div>}
          <button className="primary-action" type="submit">
            {mode === "login" ? "Enter command" : "Create account"} <ArrowRight size={18} />
          </button>
        </form>
      </section>
    </main>
  );
}

function HudCard({ icon: Icon, label, value, detail, tone = "blue" }) {
  return (
    <div className={`hud-card ${tone}`}>
      <div className="hud-icon">
        <Icon size={18} />
      </div>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function StatusPill({ status }) {
  const normalized = status.toLowerCase();
  return <span className={`status-pill ${normalized}`}>{status}</span>;
}

function ToolPanel({ activeTab }) {
  const content = {
    macro: {
      icon: Landmark,
      title: "Macro Engine",
      body: "Strict IBM/Qiskit macro pipeline, Alpaca paper-order adapter, and PostgreSQL telemetry store.",
      command: "py -3.11 strict_macro_quantum_v10.py --preflight",
    },
    grants: {
      icon: GraduationCap,
      title: "Grants Optimizer",
      body: "Ranks real grant, scholarship, and emergency-aid opportunities from the local CSV tracker.",
      command: "python grants.py rank",
    },
    housing: {
      icon: Home,
      title: "Housing Log",
      body: "Builds an evidence summary for unresolved housing issues and urgent repair records.",
      command: "python housing_violations.py summarize",
    },
    catalog: {
      icon: Gem,
      title: "Item Catalog",
      body: "Turns comparable sale ranges into a conservative collectible catalog and paper estimate sheet.",
      command: "python shell_catalog.py estimate",
    },
  }[activeTab];
  const Icon = content.icon;

  return (
    <section className="tool-panel">
      <div className="tool-mark">
        <Icon size={20} />
      </div>
      <div>
        <p className="eyebrow">Operational module</p>
        <h2>{content.title}</h2>
        <p>{content.body}</p>
        <code>{content.command}</code>
      </div>
    </section>
  );
}

function Dashboard({ user, onLogout }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("macro");

  useEffect(() => {
    api("/api/portfolio").then(setData).catch((err) => setError(err.message));
  }, []);

  const assets = data?.assets || [];
  const summary = data?.summary || {};
  const chartData = useMemo(
    () =>
      assets.map((asset, index) => ({
        ticker: asset.ticker,
        weight: Number(asset.target_weight),
        percent: Number(asset.target_weight) * 100,
        commandCash: Number(asset.target_weight) * COMMAND_CAPITAL,
        cash: Number(asset.paper_cash),
        risk: Number(asset.volatility) * 100,
        return: Number(asset.expected_return) * 100,
        fill: COLORS[index % COLORS.length],
      })),
    [assets],
  );

  const riskCurve = useMemo(
    () =>
      chartData.map((asset, index) => ({
        name: asset.ticker,
        exposure: Number((asset.percent * (1 + index * 0.04)).toFixed(2)),
        risk: Number(asset.risk.toFixed(2)),
        return: Number(asset.return.toFixed(2)),
      })),
    [chartData],
  );

  const riskVectors = [
    { label: "Volatility exposure", value: `${((summary.weightedRisk || 0) * 100).toFixed(2)}%`, status: "Watch" },
    { label: "Capital concentration", value: `${Math.max(...chartData.map((asset) => asset.percent), 0).toFixed(2)}%`, status: "Pass" },
    { label: "Broker execution", value: "Paper only", status: "Pass" },
    { label: "Model drift", value: "CSV seed", status: "Watch" },
  ];

  const gates = [
    { gate: "JWT auth boundary", owner: "API", status: "Pass" },
    { gate: "PostgreSQL pool", owner: "Backend", status: "Ready" },
    { gate: "Alpaca live trading", owner: "Broker", status: "Blocked" },
    { gate: "IBM runtime instance", owner: "Quantum", status: "Ready" },
    { gate: "Rate-limit shield", owner: "Gateway", status: "Pass" },
  ];

  return (
    <main className="command-shell">
      <aside className="side-rail">
        <div className="rail-brand">
          <CircuitBoard size={23} />
        </div>
        <button className={activeTab === "macro" ? "rail-active" : ""} onClick={() => setActiveTab("macro")} title="Macro Engine">
          <Landmark size={20} />
        </button>
        <button className={activeTab === "grants" ? "rail-active" : ""} onClick={() => setActiveTab("grants")} title="Grants Optimizer">
          <GraduationCap size={20} />
        </button>
        <button className={activeTab === "housing" ? "rail-active" : ""} onClick={() => setActiveTab("housing")} title="Housing Log">
          <Home size={20} />
        </button>
        <button className={activeTab === "catalog" ? "rail-active" : ""} onClick={() => setActiveTab("catalog")} title="Item Catalog">
          <Gem size={20} />
        </button>
      </aside>

      <section className="command-main">
        <header className="command-topbar">
          <div>
            <p className="eyebrow">Data-Analytics / Repo 52</p>
            <h1>Macro Asset Command Center</h1>
          </div>
          <div className="operator-block">
            <span>{user.displayName}</span>
            <button className="ghost-button" onClick={onLogout} type="button">
              <LogOut size={17} /> Sign out
            </button>
          </div>
        </header>

        {error && <div className="error-line">{error}</div>}
        {!data && !error && <div className="loading-panel">Loading command telemetry...</div>}

        {data && (
          <>
            <section className="hud-grid">
              <HudCard icon={Landmark} label="Command capital" value="$500,000" detail="institutional sandbox boundary" tone="blue" />
              <HudCard icon={BarChart3} label="Weighted return" value={`${((summary.weightedReturn || 0) * 100).toFixed(2)}%`} detail="model input estimate" tone="green" />
              <HudCard icon={Gauge} label="Weighted risk" value={`${((summary.weightedRisk || 0) * 100).toFixed(2)}%`} detail="mathematical exposure" tone="orange" />
              <HudCard icon={Database} label="Telemetry assets" value={summary.assetCount || 0} detail="PostgreSQL portfolio layer" tone="violet" />
            </section>

            <section className="ticker-strip">
              {chartData.map((asset) => (
                <div className="ticker-cell" key={asset.ticker}>
                  <strong>{asset.ticker}</strong>
                  <span>${asset.commandCash.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                  <small>{asset.percent.toFixed(2)}% target</small>
                </div>
              ))}
            </section>

            <section className="control-grid">
              <div className="control-panel span-2">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Risk analysis curve</p>
                    <h2>Return / Volatility / Exposure</h2>
                  </div>
                  <Zap size={18} />
                </div>
                <ResponsiveContainer width="100%" height={310}>
                  <LineChart data={riskCurve}>
                    <CartesianGrid stroke="#263244" strokeDasharray="3 5" vertical={false} />
                    <XAxis dataKey="name" stroke="#7c8aa5" />
                    <YAxis stroke="#7c8aa5" />
                    <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #233049", color: "#e5edf7" }} />
                    <Line type="monotone" dataKey="return" stroke="#22c55e" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="risk" stroke="#f97316" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="exposure" stroke="#38bdf8" strokeWidth={3} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="control-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Allocation wheel</p>
                    <h2>Capital Distribution</h2>
                  </div>
                  <PieChart size={18} />
                </div>
                <ResponsiveContainer width="100%" height={280}>
                  <RePieChart>
                    <Pie data={chartData} dataKey="commandCash" nameKey="ticker" innerRadius={58} outerRadius={100} paddingAngle={4}>
                      {chartData.map((entry) => (
                        <Cell key={entry.ticker} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #233049", color: "#e5edf7" }} formatter={(value) => `$${Number(value).toFixed(2)}`} />
                  </RePieChart>
                </ResponsiveContainer>
              </div>

              <div className="control-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Deployment risk vectors</p>
                    <h2>System Change Posture</h2>
                  </div>
                  <AlertTriangle size={18} />
                </div>
                <div className="vector-stack">
                  {riskVectors.map((vector) => (
                    <div className="vector-row" key={vector.label}>
                      <span>{vector.label}</span>
                      <strong>{vector.value}</strong>
                      <StatusPill status={vector.status} />
                    </div>
                  ))}
                </div>
              </div>

              <div className="control-panel span-2">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Policy compliance gate ledger</p>
                    <h2>Production Readiness Gates</h2>
                  </div>
                  <ShieldCheck size={18} />
                </div>
                <div className="gate-table">
                  {gates.map((gate) => (
                    <div className="gate-row" key={gate.gate}>
                      <CheckCircle2 size={17} />
                      <span>{gate.gate}</span>
                      <small>{gate.owner}</small>
                      <StatusPill status={gate.status} />
                    </div>
                  ))}
                </div>
              </div>

              <div className="control-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">Capital grid</p>
                    <h2>Asset Ledger</h2>
                  </div>
                  <Boxes size={18} />
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={chartData}>
                    <CartesianGrid stroke="#263244" strokeDasharray="3 5" vertical={false} />
                    <XAxis dataKey="ticker" stroke="#7c8aa5" />
                    <YAxis stroke="#7c8aa5" />
                    <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #233049", color: "#e5edf7" }} />
                    <Bar dataKey="percent" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry) => (
                        <Cell key={entry.ticker} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="module-tabs">
              <button className={activeTab === "macro" ? "active" : ""} onClick={() => setActiveTab("macro")} type="button">
                <Landmark size={17} /> Macro
              </button>
              <button className={activeTab === "grants" ? "active" : ""} onClick={() => setActiveTab("grants")} type="button">
                <GraduationCap size={17} /> Grants
              </button>
              <button className={activeTab === "housing" ? "active" : ""} onClick={() => setActiveTab("housing")} type="button">
                <Home size={17} /> Housing
              </button>
              <button className={activeTab === "catalog" ? "active" : ""} onClick={() => setActiveTab("catalog")} type="button">
                <FileSearch size={17} /> Catalog
              </button>
            </section>
            <ToolPanel activeTab={activeTab} />
          </>
        )}
      </section>
    </main>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    api("/api/me")
      .then((payload) => setUser(payload.user))
      .finally(() => setChecking(false));
  }, []);

  async function logout() {
    await api("/api/logout", { method: "POST", body: "{}" });
    setUser(null);
  }

  if (checking) return <main className="loading-panel full">Checking session...</main>;
  return user ? <Dashboard user={user} onLogout={logout} /> : <AuthPanel onAuth={setUser} />;
}

createRoot(document.getElementById("root")).render(<App />);
