import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowRight,
  BarChart3,
  CircuitBoard,
  Lock,
  LogOut,
  PieChart,
  ShieldCheck,
  UserPlus,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Pie,
  PieChart as RePieChart,
} from "recharts";
import "./styles.css";

const COLORS = ["#1d4ed8", "#0f766e", "#c2410c", "#7c3aed", "#be123c", "#166534"];

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
        <p className="eyebrow">Private telemetry command</p>
        <h1>Portfolio intelligence, locked per user.</h1>
        <p className="auth-copy">
          Sign in to load a personal paper portfolio, chart the allocation matrix, and keep each account separated in SQLite.
        </p>
        <div className="security-row">
          <ShieldCheck size={18} />
          <span>PBKDF2 password hashing</span>
        </div>
        <div className="security-row">
          <Lock size={18} />
          <span>HttpOnly session cookies</span>
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
            {mode === "login" ? "Open dashboard" : "Create account"} <ArrowRight size={18} />
          </button>
        </form>
      </section>
    </main>
  );
}

function Metric({ icon: Icon, label, value, detail }) {
  return (
    <div className="metric">
      <div className="metric-icon">
        <Icon size={18} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </div>
  );
}

function Dashboard({ user, onLogout }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/portfolio").then(setData).catch((err) => setError(err.message));
  }, []);

  const assets = data?.assets || [];
  const summary = data?.summary || {};
  const chartData = useMemo(
    () =>
      assets.map((asset) => ({
        ticker: asset.ticker,
        weight: Number(asset.target_weight),
        percent: Number(asset.target_weight) * 100,
        cash: Number(asset.paper_cash),
        risk: Number(asset.volatility) * 100,
        return: Number(asset.expected_return) * 100,
      })),
    [assets],
  );

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Quantum portfolio command</p>
          <h1>{user.displayName}'s telemetry</h1>
        </div>
        <button className="ghost-button" onClick={onLogout} type="button">
          <LogOut size={17} /> Sign out
        </button>
      </header>

      {error && <div className="error-line">{error}</div>}
      {!data && !error && <div className="loading-panel">Loading portfolio telemetry...</div>}

      {data && (
        <>
          <section className="metrics-grid">
            <Metric icon={Activity} label="Paper capital" value={`$${summary.totalCash.toLocaleString()}`} detail="seeded per user" />
            <Metric icon={BarChart3} label="Weighted return" value={`${(summary.weightedReturn * 100).toFixed(2)}%`} detail="input model estimate" />
            <Metric icon={PieChart} label="Weighted risk" value={`${(summary.weightedRisk * 100).toFixed(2)}%`} detail="diagonal risk model" />
          </section>

          <section className="chart-grid">
            <div className="chart-panel wide">
              <div className="panel-heading">
                <h2>Allocation Matrix</h2>
                <span>Paper target weights</span>
              </div>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="ticker" />
                  <YAxis />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)}%`} />
                  <Bar dataKey="percent" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={entry.ticker} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-panel">
              <div className="panel-heading">
                <h2>Capital Split</h2>
                <span>Cash by asset</span>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <RePieChart>
                  <Pie data={chartData} dataKey="cash" nameKey="ticker" innerRadius={58} outerRadius={96} paddingAngle={4}>
                    {chartData.map((entry, index) => (
                      <Cell key={entry.ticker} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `$${Number(value).toFixed(2)}`} />
                </RePieChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-panel">
              <div className="panel-heading">
                <h2>Risk / Return</h2>
                <span>Model inputs</span>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="ticker" />
                  <YAxis />
                  <Tooltip formatter={(value) => `${Number(value).toFixed(2)}%`} />
                  <Area dataKey="return" stroke="#0f766e" fill="#99f6e4" fillOpacity={0.55} />
                  <Area dataKey="risk" stroke="#c2410c" fill="#fed7aa" fillOpacity={0.45} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="ledger-panel">
            <div className="panel-heading">
              <h2>Per-User Ledger</h2>
              <span>{summary.assetCount} assets</span>
            </div>
            <div className="ledger-table">
              <div className="ledger-head">
                <span>Ticker</span>
                <span>Weight</span>
                <span>Paper Cash</span>
                <span>Return</span>
                <span>Risk</span>
              </div>
              {chartData.map((asset) => (
                <div className="ledger-row" key={asset.ticker}>
                  <strong>{asset.ticker}</strong>
                  <span>{asset.percent.toFixed(2)}%</span>
                  <span>${asset.cash.toFixed(2)}</span>
                  <span>{asset.return.toFixed(2)}%</span>
                  <span>{asset.risk.toFixed(2)}%</span>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
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
