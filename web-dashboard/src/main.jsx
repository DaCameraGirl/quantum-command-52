import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Building2,
  Boxes,
  CalendarClock,
  CheckCircle2,
  CircuitBoard,
  Database,
  DollarSign,
  FileSearch,
  Gauge,
  Gem,
  GraduationCap,
  Home,
  Landmark,
  Lock,
  LogOut,
  MapPin,
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

const PIPELINE_DEALS = [
  {
    id: "TX-1042",
    stage: "listing",
    address: "418 Harbor View Lane",
    city: "Charleston",
    state: "SC",
    price: 485000,
    agent: "Angela",
    client: "Seller file",
    escrow: "Pending offer",
    earnestMoney: 0,
    closingOffset: 42,
    milestones: [
      { name: "Seller disclosure packet", offset: 2, completed: false, critical: true },
      { name: "MLS photo review", offset: 4, completed: false, critical: false },
      { name: "Offer review window", offset: 9, completed: false, critical: true },
    ],
  },
  {
    id: "TX-1077",
    stage: "under_contract",
    address: "92 Cedar Mill Court",
    city: "Raleigh",
    state: "NC",
    price: 612500,
    agent: "Angela",
    client: "Buyer file",
    escrow: "Atlantic Title",
    earnestMoney: 18500,
    closingOffset: 28,
    milestones: [
      { name: "Inspection contingency", offset: 1, completed: false, critical: true },
      { name: "Appraisal ordered", offset: 5, completed: false, critical: true },
      { name: "Loan approval deadline", offset: 13, completed: false, critical: true },
    ],
  },
  {
    id: "TX-1091",
    stage: "under_contract",
    address: "733 Market Row",
    city: "Atlanta",
    state: "GA",
    price: 748000,
    agent: "Angela",
    client: "Investor file",
    escrow: "Secure Escrow Co.",
    earnestMoney: 25000,
    closingOffset: 18,
    milestones: [
      { name: "HOA document review", offset: -1, completed: false, critical: true },
      { name: "Financing condition", offset: 6, completed: false, critical: true },
      { name: "Final walkthrough", offset: 16, completed: false, critical: false },
    ],
  },
  {
    id: "TX-1103",
    stage: "closing",
    address: "1509 Ridgecrest Avenue",
    city: "Nashville",
    state: "TN",
    price: 524900,
    agent: "Angela",
    client: "Relocation file",
    escrow: "Keystone Settlement",
    earnestMoney: 16000,
    closingOffset: 5,
    milestones: [
      { name: "Clear to close", offset: 0, completed: false, critical: true },
      { name: "Wire instructions verified", offset: 2, completed: false, critical: true },
      { name: "Closing appointment", offset: 5, completed: false, critical: true },
    ],
  },
  {
    id: "TX-1019",
    stage: "closed",
    address: "21 Maple Station Drive",
    city: "Charlotte",
    state: "NC",
    price: 389000,
    agent: "Angela",
    client: "Closed buyer file",
    escrow: "Closed",
    earnestMoney: 12000,
    closingOffset: -8,
    milestones: [
      { name: "Inspection contingency", offset: -27, completed: true, critical: true },
      { name: "Loan approval deadline", offset: -18, completed: true, critical: true },
      { name: "Recorded closing", offset: -8, completed: true, critical: true },
    ],
  },
];

const PIPELINE_COLUMNS = [
  { id: "listing", title: "Listing", tone: "blue" },
  { id: "under_contract", title: "Under Contract", tone: "orange" },
  { id: "closing", title: "Closing", tone: "violet" },
  { id: "closed", title: "Closed", tone: "green" },
];

function shiftedDate(offsetDays) {
  const date = new Date();
  date.setHours(12, 0, 0, 0);
  date.setDate(date.getDate() + offsetDays);
  return date;
}

function formatShortDate(date) {
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function daysUntil(date) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(date);
  target.setHours(0, 0, 0, 0);
  return Math.round((target - today) / 86400000);
}

function milestoneRisk(milestone) {
  if (milestone.completed) return "complete";
  const days = daysUntil(milestone.dueDate);
  if (days < 0) return "breach";
  if (milestone.critical && days <= 2) return "critical";
  if (days <= 7) return "watch";
  return "clear";
}

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

function TransactionPipelineBoard() {
  const [sourceDeals, setSourceDeals] = useState(PIPELINE_DEALS);
  const [summary, setSummary] = useState({
    activeDealValue: 0,
    earnestExposure: 0,
    deadlineBreachCount: 0,
    dueThisWeekCount: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadTransactions() {
    setError("");
    setLoading(true);
    try {
      const payload = await api("/api/transactions");
      setSourceDeals(payload.deals || []);
      setSummary(payload.summary || {});
    } catch (err) {
      setError(`${err.message}. Showing local sample transaction data.`);
      setSourceDeals(PIPELINE_DEALS);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTransactions();
  }, []);

  async function moveDealStage(deal, newStage) {
    if (deal.stage === newStage) return;
    const originalDeals = sourceDeals;
    setError("");
    setSourceDeals((currentDeals) =>
      currentDeals.map((item) =>
        item.transactionId === deal.transactionId || item.id === deal.id
          ? { ...item, stage: newStage }
          : item,
      ),
    );

    try {
      await api(`/api/transactions/${deal.transactionId || deal.id}/stage`, {
        method: "PATCH",
        body: JSON.stringify({ stage: newStage }),
      });
      await loadTransactions();
    } catch (err) {
      setSourceDeals(originalDeals);
      setError(`Stage update failed: ${err.message}`);
    }
  }

  const deals = useMemo(
    () =>
      sourceDeals.map((deal) => {
        const closingDate = deal.closingDate ? new Date(deal.closingDate) : shiftedDate(deal.closingOffset || 0);
        const milestones = (deal.milestones || []).map((milestone) => {
          const dueDate = milestone.dueDate ? new Date(milestone.dueDate) : shiftedDate(milestone.offset || 0);
          return {
            ...milestone,
            name: milestone.name || milestone.milestone_name,
            dueDate,
            dueIn: daysUntil(dueDate),
            completed: Boolean(milestone.completed),
            critical: Boolean(milestone.critical),
          };
        });
        const openCritical = milestones.filter((milestone) => milestone.critical && !milestone.completed);
        const nextMilestone = milestones
          .filter((milestone) => !milestone.completed)
          .sort((a, b) => a.dueDate - b.dueDate)[0];
        const worstRisk = milestones.reduce((current, milestone) => {
          const risk = milestoneRisk(milestone);
          const rank = { complete: 0, clear: 1, watch: 2, critical: 3, breach: 4 };
          return rank[risk] > rank[current] ? risk : current;
        }, "complete");

        return {
          ...deal,
          closingDate,
          milestones,
          price: Number(deal.price || 0),
          earnestMoney: Number(deal.earnestMoney || 0),
          openCriticalCount: openCritical.length,
          nextMilestone,
          risk: worstRisk,
        };
      }),
    [sourceDeals],
  );

  const activeDeals = deals.filter((deal) => deal.stage !== "closed");
  const dealValue = Number(summary.activeDealValue || activeDeals.reduce((total, deal) => total + deal.price, 0));
  const earnestExposure = Number(summary.earnestExposure || activeDeals.reduce((total, deal) => total + deal.earnestMoney, 0));
  const breachedMilestones = deals.flatMap((deal) => deal.milestones.filter((milestone) => milestoneRisk(milestone) === "breach"));
  const dueSoon = deals.flatMap((deal) => deal.milestones.filter((milestone) => !milestone.completed && milestone.dueIn >= 0 && milestone.dueIn <= 7));
  const timelineData = deals
    .filter((deal) => deal.stage !== "closed")
    .map((deal) => ({
      name: deal.id.replace("TX-", "#"),
      days: Math.max(daysUntil(deal.closingDate), 0),
      value: Math.round(deal.price / 1000),
    }));

  return (
    <section className="transaction-room">
      <div className="grant-head">
        <div>
          <p className="eyebrow">Real estate transaction control</p>
          <h2>Deal Pipeline Board</h2>
          <p>Stage tracking for listings, active contracts, closing files, and contingency windows.</p>
        </div>
        <button className="ghost-button" onClick={loadTransactions} type="button">
          <CalendarClock size={16} /> Refresh audit
        </button>
      </div>

      {error && <div className="error-line">{error}</div>}
      {loading && <div className="grant-empty">Loading transaction pipeline from PostgreSQL...</div>}

      <div className="grant-summary-grid">
        <HudCard icon={Building2} label="Active deal value" value={`$${dealValue.toLocaleString()}`} detail={`${activeDeals.length} open files`} tone="blue" />
        <HudCard icon={DollarSign} label="Earnest exposure" value={`$${earnestExposure.toLocaleString()}`} detail="deposit at risk" tone="orange" />
        <HudCard icon={AlertTriangle} label="Deadline breaches" value={summary.deadlineBreachCount ?? breachedMilestones.length} detail="requires action" tone="violet" />
        <HudCard icon={CheckCircle2} label="Due this week" value={summary.dueThisWeekCount ?? dueSoon.length} detail="open milestones" tone="green" />
      </div>

      <section className="deal-intel-grid">
        <div className="transaction-chart">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Closing runway</p>
              <h2>Days Until Target Close</h2>
            </div>
            <BarChart3 size={18} />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={timelineData}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke="#7c8aa5" />
              <YAxis stroke="#7c8aa5" />
              <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #233049", color: "#e5edf7" }} />
              <Bar dataKey="days" fill="#38bdf8" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="deadline-ledger">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Critical windows</p>
              <h2>Contingency Ledger</h2>
            </div>
            <AlertTriangle size={18} />
          </div>
          {deals
            .flatMap((deal) =>
              deal.milestones.map((milestone) => ({
                ...milestone,
                dealId: deal.id,
                address: deal.address,
                risk: milestoneRisk(milestone),
              })),
            )
            .sort((a, b) => a.dueDate - b.dueDate)
            .slice(0, 7)
            .map((milestone) => (
              <div className={`deadline-row ${milestone.risk}`} key={`${milestone.dealId}-${milestone.name}`}>
                <div>
                  <strong>{milestone.name}</strong>
                  <span>{milestone.dealId} / {milestone.address}</span>
                </div>
                <div>
                  <b>{formatShortDate(milestone.dueDate)}</b>
                  <StatusPill status={milestone.risk} />
                </div>
              </div>
            ))}
        </div>
      </section>

      <section className="pipeline-board" aria-label="Real estate transaction pipeline board">
        {PIPELINE_COLUMNS.map((column) => {
          const columnDeals = deals.filter((deal) => deal.stage === column.id);
          return (
            <div
              className={`pipeline-column ${column.tone}`}
              key={column.id}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                const transactionId = event.dataTransfer.getData("text/plain");
                const draggedDeal = deals.find((deal) => String(deal.transactionId || deal.id) === transactionId);
                if (draggedDeal) moveDealStage(draggedDeal, column.id);
              }}
            >
              <div className="pipeline-column-head">
                <h3>{column.title}</h3>
                <span>{columnDeals.length}</span>
              </div>
              {columnDeals.map((deal) => (
                <article
                  className={`deal-card ${deal.risk}`}
                  draggable
                  key={deal.id}
                  onDragStart={(event) => {
                    event.dataTransfer.effectAllowed = "move";
                    event.dataTransfer.setData("text/plain", String(deal.transactionId || deal.id));
                  }}
                >
                  <div className="deal-card-head">
                    <div>
                      <p className="eyebrow">{deal.id}</p>
                      <h4>{deal.address}</h4>
                    </div>
                    <StatusPill status={deal.risk} />
                  </div>
                  <div className="deal-location">
                    <MapPin size={14} />
                    <span>{deal.city}, {deal.state}</span>
                  </div>
                  <div className="deal-metrics">
                    <span>
                      <b>${deal.price.toLocaleString()}</b>
                      Contract value
                    </span>
                    <span>
                      <b>{formatShortDate(deal.closingDate)}</b>
                      Target close
                    </span>
                  </div>
                  <div className="next-window">
                    <span>{deal.nextMilestone?.name || "File complete"}</span>
                    <strong>{deal.nextMilestone ? `${deal.nextMilestone.dueIn}d` : "Done"}</strong>
                  </div>
                  <div className="deal-foot">
                    <small>{deal.escrow}</small>
                    <small>{deal.openCriticalCount} critical open</small>
                  </div>
                </article>
              ))}
            </div>
          );
        })}
      </section>
    </section>
  );
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

  if (activeTab === "transactions") {
    return <TransactionPipelineBoard />;
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
        <button className={activeTab === "transactions" ? "rail-active" : ""} onClick={() => setActiveTab("transactions")} title="Transaction Pipeline">
          <Building2 size={20} />
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
