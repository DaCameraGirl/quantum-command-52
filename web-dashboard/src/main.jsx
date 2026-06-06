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
  Plus,
  Printer,
  RefreshCw,
  ShieldCheck,
  Trash2,
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

function GrantOptimizer() {
  const [grants, setGrants] = useState([]);
  const [summary, setSummary] = useState({ grantCount: 0, activeGrantCount: 0, totalFunding: 0, topPriorityScore: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    grantName: "",
    fundingAmount: "5000",
    deadline: "",
    applicationDifficulty: "3",
    status: "research",
  });

  async function loadGrants() {
    setError("");
    setLoading(true);
    try {
      const payload = await api("/api/grants");
      setGrants(payload.grants || []);
      setSummary(payload.summary || {});
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadGrants();
  }, []);

  async function submitGrant(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/api/grants", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          fundingAmount: Number(form.fundingAmount),
          applicationDifficulty: Number(form.applicationDifficulty),
        }),
      });
      setForm({
        grantName: "",
        fundingAmount: "5000",
        deadline: "",
        applicationDifficulty: "3",
        status: "research",
      });
      await loadGrants();
    } catch (err) {
      setError(err.message);
    }
  }

  async function updateGrant(grant, patch) {
    setError("");
    try {
      await api(`/api/grants/${grant.id}`, {
        method: "PUT",
        body: JSON.stringify({
          grantName: grant.grant_name,
          fundingAmount: Number(grant.funding_amount),
          deadline: grant.deadline || "",
          applicationDifficulty: Number(grant.application_difficulty),
          status: grant.status,
          ...patch,
        }),
      });
      await loadGrants();
    } catch (err) {
      setError(err.message);
    }
  }

  async function deleteGrant(grantId) {
    setError("");
    try {
      await api(`/api/grants/${grantId}`, { method: "DELETE" });
      await loadGrants();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="grant-console">
      <div className="grant-head">
        <div>
          <p className="eyebrow">Live PostgreSQL module</p>
          <h2>Grants Optimizer Ledger</h2>
          <p>Authenticated CRUD with automatic priority scoring from amount, deadline, difficulty, and status.</p>
        </div>
        <button className="ghost-button" onClick={loadGrants} type="button">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {error && <div className="error-line">{error}</div>}

      <div className="grant-summary-grid">
        <HudCard icon={GraduationCap} label="Tracked grants" value={summary.grantCount || 0} detail="user ledger rows" tone="blue" />
        <HudCard icon={CheckCircle2} label="Active grants" value={summary.activeGrantCount || 0} detail="not denied or archived" tone="green" />
        <HudCard
          icon={Landmark}
          label="Funding pipeline"
          value={`$${Number(summary.totalFunding || 0).toLocaleString()}`}
          detail="active total"
          tone="orange"
        />
        <HudCard icon={Gauge} label="Top priority" value={Number(summary.topPriorityScore || 0).toFixed(2)} detail="server-ranked score" tone="violet" />
      </div>

      <form className="grant-form" onSubmit={submitGrant}>
        <label>
          Grant name
          <input value={form.grantName} onChange={(event) => setForm({ ...form, grantName: event.target.value })} placeholder="Emergency education aid" />
        </label>
        <label>
          Funding amount
          <input
            value={form.fundingAmount}
            onChange={(event) => setForm({ ...form, fundingAmount: event.target.value })}
            type="number"
            min="0"
            step="100"
          />
        </label>
        <label>
          Deadline
          <input value={form.deadline} onChange={(event) => setForm({ ...form, deadline: event.target.value })} type="date" />
        </label>
        <label>
          Difficulty
          <select value={form.applicationDifficulty} onChange={(event) => setForm({ ...form, applicationDifficulty: event.target.value })}>
            <option value="1">1 - Easy</option>
            <option value="2">2 - Light</option>
            <option value="3">3 - Standard</option>
            <option value="4">4 - Heavy</option>
            <option value="5">5 - Complex</option>
          </select>
        </label>
        <label>
          Status
          <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
            <option value="research">Research</option>
            <option value="ready">Ready</option>
            <option value="applied">Applied</option>
            <option value="follow_up">Follow up</option>
            <option value="approved">Approved</option>
            <option value="denied">Denied</option>
            <option value="archived">Archived</option>
          </select>
        </label>
        <button className="primary-action" type="submit">
          <Plus size={17} /> Add and rank
        </button>
      </form>

      <div className="grant-table">
        <div className="grant-row grant-row-head">
          <span>Grant</span>
          <span>Amount</span>
          <span>Deadline</span>
          <span>Difficulty</span>
          <span>Priority</span>
          <span>Status</span>
          <span></span>
        </div>
        {loading && <div className="grant-empty">Loading grant ledger...</div>}
        {!loading && grants.length === 0 && <div className="grant-empty">No grants yet. Add the first opportunity above.</div>}
        {!loading &&
          grants.map((grant) => (
            <div className="grant-row" key={grant.id}>
              <strong>{grant.grant_name}</strong>
              <span>${Number(grant.funding_amount).toLocaleString()}</span>
              <span>{grant.deadline || "No deadline"}</span>
              <select
                value={String(grant.application_difficulty)}
                onChange={(event) => updateGrant(grant, { applicationDifficulty: Number(event.target.value) })}
                aria-label={`Difficulty for ${grant.grant_name}`}
              >
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5</option>
              </select>
              <span className="priority-score">{Number(grant.priority_score).toFixed(2)}</span>
              <select value={grant.status} onChange={(event) => updateGrant(grant, { status: event.target.value })} aria-label={`Status for ${grant.grant_name}`}>
                <option value="research">Research</option>
                <option value="ready">Ready</option>
                <option value="applied">Applied</option>
                <option value="follow_up">Follow up</option>
                <option value="approved">Approved</option>
                <option value="denied">Denied</option>
                <option value="archived">Archived</option>
              </select>
              <button className="icon-button danger" onClick={() => deleteGrant(grant.id)} type="button" aria-label={`Delete ${grant.grant_name}`}>
                <Trash2 size={16} />
              </button>
            </div>
          ))}
      </div>
    </section>
  );
}

function HousingEvidenceVault() {
  const [incidents, setIncidents] = useState([]);
  const [summary, setSummary] = useState({ incidentCount: 0, openIncidentCount: 0, overdueCount: 0, maxDaysUnresolved: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    category: "Maintenance",
    description: "",
    areaLocation: "",
    requestDate: new Date().toISOString().slice(0, 10),
    resolveDate: "",
    severityLevel: "5",
    status: "open",
  });

  async function loadIncidents() {
    setError("");
    setLoading(true);
    try {
      const payload = await api("/api/housing");
      setIncidents(payload.incidents || []);
      setSummary(payload.summary || {});
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadIncidents();
  }, []);

  async function submitIncident(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/api/housing", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          severityLevel: Number(form.severityLevel),
        }),
      });
      setForm({
        category: "Maintenance",
        description: "",
        areaLocation: "",
        requestDate: new Date().toISOString().slice(0, 10),
        resolveDate: "",
        severityLevel: "5",
        status: "open",
      });
      await loadIncidents();
    } catch (err) {
      setError(err.message);
    }
  }

  async function updateIncident(incident, patch) {
    setError("");
    try {
      await api(`/api/housing/${incident.incident_id}`, {
        method: "PUT",
        body: JSON.stringify({
          category: incident.category,
          description: incident.description,
          areaLocation: incident.area_location,
          requestDate: incident.request_date,
          resolveDate: incident.resolve_date || "",
          severityLevel: Number(incident.severity_level),
          status: incident.status,
          ...patch,
        }),
      });
      await loadIncidents();
    } catch (err) {
      setError(err.message);
    }
  }

  async function deleteIncident(incidentId) {
    setError("");
    try {
      await api(`/api/housing/${incidentId}`, { method: "DELETE" });
      await loadIncidents();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="housing-vault">
      <div className="grant-head">
        <div>
          <p className="eyebrow">Evidence vault</p>
          <h2>Housing Incident Timeline</h2>
          <p>Authenticated incident tracking with days-unresolved calculations and severity-based violation flags.</p>
        </div>
        <div className="vault-actions">
          <button className="ghost-button" onClick={loadIncidents} type="button">
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="ghost-button print-button" onClick={() => window.print()} type="button">
            <Printer size={16} /> Print
          </button>
        </div>
      </div>

      {error && <div className="error-line">{error}</div>}

      <div className="grant-summary-grid">
        <HudCard icon={Home} label="Logged incidents" value={summary.incidentCount || 0} detail="evidence records" tone="blue" />
        <HudCard icon={AlertTriangle} label="Open issues" value={summary.openIncidentCount || 0} detail="not resolved or closed" tone="orange" />
        <HudCard icon={ShieldCheck} label="Overdue flags" value={summary.overdueCount || 0} detail="timeline alerts" tone="violet" />
        <HudCard icon={Gauge} label="Max unresolved" value={`${summary.maxDaysUnresolved || 0}d`} detail="open timeline" tone="green" />
      </div>

      <form className="housing-form" onSubmit={submitIncident}>
        <label>
          Category
          <select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}>
            <option>Maintenance</option>
            <option>Safety</option>
            <option>Utilities</option>
            <option>Pest</option>
            <option>Access</option>
            <option>Lease</option>
          </select>
        </label>
        <label>
          Area / location
          <input value={form.areaLocation} onChange={(event) => setForm({ ...form, areaLocation: event.target.value })} placeholder="Kitchen ceiling" />
        </label>
        <label>
          Request date
          <input value={form.requestDate} onChange={(event) => setForm({ ...form, requestDate: event.target.value })} type="date" />
        </label>
        <label>
          Severity
          <select value={form.severityLevel} onChange={(event) => setForm({ ...form, severityLevel: event.target.value })}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
            <option value="open">Open</option>
            <option value="requested">Requested</option>
            <option value="scheduled">Scheduled</option>
            <option value="escalated">Escalated</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </label>
        <label className="housing-description">
          Description
          <input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Document what happened, who was notified, and visible impact" />
        </label>
        <button className="primary-action" type="submit">
          <Plus size={17} /> Add incident
        </button>
      </form>

      <div className="timeline-deck">
        {loading && <div className="grant-empty">Loading housing timeline...</div>}
        {!loading && incidents.length === 0 && <div className="grant-empty">No incidents logged yet. Add the first record above.</div>}
        {!loading &&
          incidents.map((incident) => (
            <article className={`timeline-card ${incident.violation_flag}`} key={incident.incident_id}>
              <div className="timeline-main">
                <div>
                  <p className="eyebrow">{incident.category} / {incident.area_location}</p>
                  <h3>{incident.description}</h3>
                </div>
                <div className="days-counter">
                  <strong>{incident.days_unresolved}</strong>
                  <span>days</span>
                </div>
              </div>
              <div className="timeline-meta">
                <span>Requested {incident.request_date}</span>
                <span>{incident.resolve_date ? `Resolved ${incident.resolve_date}` : "Resolution pending"}</span>
                <StatusPill status={incident.violation_flag.replaceAll("_", " ")} />
              </div>
              <div className="timeline-controls">
                <label>
                  Severity
                  <select
                    value={String(incident.severity_level)}
                    onChange={(event) => updateIncident(incident, { severityLevel: Number(event.target.value) })}
                  >
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((value) => (
                      <option key={value} value={value}>{value}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Status
                  <select value={incident.status} onChange={(event) => updateIncident(incident, { status: event.target.value })}>
                    <option value="open">Open</option>
                    <option value="requested">Requested</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="escalated">Escalated</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                  </select>
                </label>
                <button className="icon-button danger" onClick={() => deleteIncident(incident.incident_id)} type="button" aria-label={`Delete incident ${incident.incident_id}`}>
                  <Trash2 size={16} />
                </button>
              </div>
            </article>
          ))}
      </div>
    </section>
  );
}

function ItemCatalogEngine() {
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState({ itemCount: 0, categoryCount: 0, totalEstimatedValue: 0, topItemValue: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    itemName: "",
    category: "Photography",
    estimatedMarketValue: "250",
    quantity: "1",
    notes: "",
  });

  async function loadInventory() {
    setError("");
    setLoading(true);
    try {
      const payload = await api("/api/inventory");
      setItems(payload.items || []);
      setSummary(payload.summary || {});
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInventory();
  }, []);

  async function submitItem(event) {
    event.preventDefault();
    setError("");
    try {
      await api("/api/inventory", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          estimatedMarketValue: Number(form.estimatedMarketValue),
          quantity: Number(form.quantity),
        }),
      });
      setForm({
        itemName: "",
        category: "Photography",
        estimatedMarketValue: "250",
        quantity: "1",
        notes: "",
      });
      await loadInventory();
    } catch (err) {
      setError(err.message);
    }
  }

  async function updateItem(item, patch) {
    setError("");
    try {
      await api(`/api/inventory/${item.item_id}`, {
        method: "PUT",
        body: JSON.stringify({
          itemName: item.item_name,
          category: item.category,
          estimatedMarketValue: Number(item.estimated_market_value),
          quantity: Number(item.quantity),
          notes: item.notes || "",
          ...patch,
        }),
      });
      await loadInventory();
    } catch (err) {
      setError(err.message);
    }
  }

  async function deleteItem(itemId) {
    setError("");
    try {
      await api(`/api/inventory/${itemId}`, { method: "DELETE" });
      await loadInventory();
    } catch (err) {
      setError(err.message);
    }
  }

  const categoryData = useMemo(() => {
    const totals = new Map();
    for (const item of items) {
      totals.set(item.category, (totals.get(item.category) || 0) + Number(item.total_estimated_value));
    }
    return Array.from(totals, ([category, value], index) => ({
      category,
      value,
      fill: COLORS[index % COLORS.length],
    })).sort((a, b) => b.value - a.value);
  }, [items]);

  return (
    <section className="inventory-engine">
      <div className="grant-head">
        <div>
          <p className="eyebrow">Physical asset engine</p>
          <h2>Item Catalog Valuation Grid</h2>
          <p>Authenticated inventory records with live valuation totals by item, category, and quantity.</p>
        </div>
        <button className="ghost-button" onClick={loadInventory} type="button">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {error && <div className="error-line">{error}</div>}

      <div className="grant-summary-grid">
        <HudCard icon={Boxes} label="Inventory items" value={summary.itemCount || 0} detail="tracked rows" tone="blue" />
        <HudCard icon={FileSearch} label="Categories" value={summary.categoryCount || 0} detail="localized groups" tone="green" />
        <HudCard
          icon={Gem}
          label="Total valuation"
          value={`$${Number(summary.totalEstimatedValue || 0).toLocaleString()}`}
          detail="market estimate"
          tone="orange"
        />
        <HudCard
          icon={Gauge}
          label="Top item"
          value={`$${Number(summary.topItemValue || 0).toLocaleString()}`}
          detail="highest total value"
          tone="violet"
        />
      </div>

      <section className="inventory-layout">
        <form className="inventory-form" onSubmit={submitItem}>
          <label>
            Item name
            <input value={form.itemName} onChange={(event) => setForm({ ...form, itemName: event.target.value })} placeholder="Camera body, lens, rare shell" />
          </label>
          <label>
            Category
            <select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}>
              <option>Photography</option>
              <option>Collectibles</option>
              <option>Electronics</option>
              <option>Jewelry</option>
              <option>Tools</option>
              <option>General</option>
            </select>
          </label>
          <label>
            Market value
            <input
              value={form.estimatedMarketValue}
              onChange={(event) => setForm({ ...form, estimatedMarketValue: event.target.value })}
              type="number"
              min="0"
              step="1"
            />
          </label>
          <label>
            Quantity
            <input value={form.quantity} onChange={(event) => setForm({ ...form, quantity: event.target.value })} type="number" min="1" step="1" />
          </label>
          <label className="inventory-notes">
            Notes
            <input value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} placeholder="Comparable source, condition, serial, location" />
          </label>
          <button className="primary-action" type="submit">
            <Plus size={17} /> Add asset
          </button>
        </form>

        <div className="inventory-chart">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Category allocation</p>
              <h2>Physical Asset Value</h2>
            </div>
            <PieChart size={18} />
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <RePieChart>
              <Pie data={categoryData} dataKey="value" nameKey="category" innerRadius={50} outerRadius={92} paddingAngle={4}>
                {categoryData.map((entry) => (
                  <Cell key={entry.category} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #233049", color: "#e5edf7" }} formatter={(value) => `$${Number(value).toFixed(2)}`} />
            </RePieChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="inventory-grid">
        {loading && <div className="grant-empty">Loading inventory valuation grid...</div>}
        {!loading && items.length === 0 && <div className="grant-empty">No assets cataloged yet. Add the first physical asset above.</div>}
        {!loading &&
          items.map((item) => (
            <article className="inventory-card" key={item.item_id}>
              <div>
                <p className="eyebrow">{item.category}</p>
                <h3>{item.item_name}</h3>
                <p>{item.notes || "No notes recorded."}</p>
              </div>
              <div className="inventory-value">
                <strong>${Number(item.total_estimated_value).toLocaleString()}</strong>
                <span>${Number(item.estimated_market_value).toLocaleString()} x {item.quantity}</span>
              </div>
              <div className="inventory-controls">
                <label>
                  Value
                  <input
                    value={String(item.estimated_market_value)}
                    onChange={(event) => updateItem(item, { estimatedMarketValue: Number(event.target.value) })}
                    type="number"
                    min="0"
                    step="1"
                  />
                </label>
                <label>
                  Qty
                  <input
                    value={String(item.quantity)}
                    onChange={(event) => updateItem(item, { quantity: Number(event.target.value) })}
                    type="number"
                    min="1"
                    step="1"
                  />
                </label>
                <button className="icon-button danger" onClick={() => deleteItem(item.item_id)} type="button" aria-label={`Delete ${item.item_name}`}>
                  <Trash2 size={16} />
                </button>
              </div>
            </article>
          ))}
      </div>
    </section>
  );
}

function ToolPanel({ activeTab }) {
  if (activeTab === "grants") {
    return <GrantOptimizer />;
  }

  if (activeTab === "housing") {
    return <HousingEvidenceVault />;
  }

  if (activeTab === "catalog") {
    return <ItemCatalogEngine />;
  }

  const content = {
    macro: {
      icon: Landmark,
      title: "Macro Engine",
      body: "Strict IBM/Qiskit macro pipeline, Alpaca paper-order adapter, and PostgreSQL telemetry store.",
      command: "py -3.11 strict_macro_quantum_v10.py --preflight",
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
