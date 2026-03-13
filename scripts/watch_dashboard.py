"""Streamlit dashboard — live-monitor a YC-Bench run.

Usage:
    uv run streamlit run scripts/watch_dashboard.py -- db/medium_1_gemini_gemini-3-flash-preview.db

Automatically overlays the greedy bot baseline if a matching *_greedy_bot.db exists
in the same directory (e.g. db/medium_1_greedy_bot.db).
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from yc_bench.db.models.client import Client, ClientTrust
from yc_bench.db.models.company import Company, CompanyPrestige
from yc_bench.db.models.employee import Employee
from yc_bench.db.models.ledger import LedgerEntry
from yc_bench.db.models.sim_state import SimState
from yc_bench.db.models.task import Task, TaskRequirement, TaskStatus
from yc_bench.db.session import build_engine, build_session_factory, session_scope
from yc_bench.config import get_world_config

# ---------------------------------------------------------------------------
# Theme colors
# ---------------------------------------------------------------------------
BG_COLOR = "#0e1117"
CARD_BG = "#1a1d23"
GRID_COLOR = "#2a2d35"
TEXT_COLOR = "#e0e0e0"
TEXT_MUTED = "#8b8d93"
ACCENT_GREEN = "#00d4aa"
ACCENT_RED = "#ff4b6e"
ACCENT_BLUE = "#4da6ff"
ACCENT_YELLOW = "#ffd43b"
ACCENT_PURPLE = "#b197fc"
ACCENT_ORANGE = "#ff8c42"

CHART_COLORS = [
    "#4da6ff", "#00d4aa", "#ff8c42", "#b197fc",
    "#ffd43b", "#ff4b6e", "#45c4b0", "#e599f7",
    "#69db7c", "#ffa94d",
]

# ---------------------------------------------------------------------------
# Page config & CSS
# ---------------------------------------------------------------------------

st.set_page_config(page_title="YC-Bench Live", layout="wide", page_icon="📊")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1a1d23 0%, #21252b 100%);
        border: 1px solid #2a2d35;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
    }
    .metric-label {
        color: #8b8d93;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e0e0e0;
        line-height: 1.2;
    }
    .metric-value.green { color: #00d4aa; }
    .metric-value.red { color: #ff4b6e; }
    .metric-value.blue { color: #4da6ff; }
    .metric-value.yellow { color: #ffd43b; }
    .metric-value.purple { color: #b197fc; }
    .section-header {
        color: #e0e0e0;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #2a2d35;
    }
    .db-path {
        color: #8b8d93;
        font-size: 0.75rem;
        font-family: monospace;
    }
    div[data-testid="stVerticalBlock"] > div { gap: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Parse DB path
# ---------------------------------------------------------------------------

db_path = None
args = sys.argv[1:]
for a in args:
    if a.endswith(".db"):
        db_path = a
        break

if db_path is None:
    st.error("Pass a .db path: `uv run streamlit run scripts/watch_dashboard.py -- path/to.db`")
    st.stop()

db_file = Path(db_path)
if not db_file.exists():
    st.error(f"DB not found: {db_file}")
    st.stop()


@st.cache_resource
def get_factory(path: str):
    engine = build_engine(f"sqlite:///{path}")
    return build_session_factory(engine)


factory = get_factory(str(db_file))

# ---------------------------------------------------------------------------
# Auto-detect greedy bot baseline DB
# ---------------------------------------------------------------------------

def _find_baseline_db(primary: Path) -> Path | None:
    """Look for a greedy_bot DB in the same directory with a matching config/seed prefix."""
    # e.g. medium_1_gemini_gemini-3-flash-preview.db -> medium_1_greedy_bot.db
    parts = primary.stem.split("_")
    if len(parts) >= 2:
        prefix = "_".join(parts[:2])  # "medium_1"
        candidate = primary.parent / f"{prefix}_greedy_bot.db"
        if candidate.exists() and candidate != primary:
            return candidate
    return None


baseline_db = _find_baseline_db(db_file)
baseline_factory = get_factory(str(baseline_db)) if baseline_db else None


def query_funds_only(fct):
    """Extract just (times, vals_dollars) from a DB factory — used for baseline overlay."""
    with session_scope(fct) as db:
        sim = db.query(SimState).first()
        if not sim:
            return [], []
        company = db.query(Company).filter(Company.id == sim.company_id).one()
        company_id = sim.company_id
        ledger = (
            db.query(LedgerEntry)
            .filter(LedgerEntry.company_id == company_id)
            .order_by(LedgerEntry.occurred_at)
            .all()
        )
        total_delta = sum(int(e.amount_cents) for e in ledger)
        initial_funds = int(company.funds_cents) - total_delta
        running = initial_funds
        times, vals = [], []
        for e in ledger:
            running += int(e.amount_cents)
            times.append(e.occurred_at)
            vals.append(running / 100)
        return times, vals


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def _chart_layout(title="", height=400, yaxis_title="", show_legend=True):
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", color=TEXT_COLOR, size=12),
        title=dict(text=title, font=dict(size=14, color=TEXT_COLOR), x=0, xanchor="left"),
        height=height,
        margin=dict(l=60, r=20, t=40, b=40),
        xaxis=dict(
            gridcolor=GRID_COLOR, zeroline=False,
            tickfont=dict(size=10, color=TEXT_MUTED),
        ),
        yaxis=dict(
            title=yaxis_title, gridcolor=GRID_COLOR, zeroline=False,
            tickfont=dict(size=10, color=TEXT_MUTED),
            title_font=dict(size=11, color=TEXT_MUTED),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(size=10, color=TEXT_MUTED),
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        ) if show_legend else dict(visible=False),
        hovermode="x unified",
    )


def _smooth(times, values, window_days=3):
    """Resample to daily frequency and apply rolling average."""
    if len(times) < 2:
        return times, values
    start, end = times[0], times[-1]
    n_days = (end - start).days
    if n_days < 2:
        return times, values
    daily_times = [start + timedelta(days=d) for d in range(n_days + 1)]
    daily_vals = []
    src_idx = 0
    for dt in daily_times:
        while src_idx < len(times) - 1 and times[src_idx + 1] <= dt:
            src_idx += 1
        daily_vals.append(values[src_idx])
    half = window_days // 2
    smoothed = []
    for i in range(len(daily_vals)):
        lo = max(0, i - half)
        hi = min(len(daily_vals), i + half + 1)
        smoothed.append(sum(daily_vals[lo:hi]) / (hi - lo))
    return daily_times, smoothed


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def query_state():
    wc = get_world_config()

    with session_scope(factory) as db:
        sim = db.query(SimState).first()
        if not sim:
            return None
        company = db.query(Company).filter(Company.id == sim.company_id).one()
        company_id = sim.company_id

        # ----- Funds time series -----
        ledger = (
            db.query(LedgerEntry)
            .filter(LedgerEntry.company_id == company_id)
            .order_by(LedgerEntry.occurred_at)
            .all()
        )
        total_delta = sum(int(e.amount_cents) for e in ledger)
        initial_funds = int(company.funds_cents) - total_delta
        running = initial_funds
        funds_times, funds_vals = [], []
        for e in ledger:
            running += int(e.amount_cents)
            funds_times.append(e.occurred_at)
            funds_vals.append(running / 100)

        # ----- Tasks -----
        tasks = db.query(Task).filter(Task.company_id == company_id).all()
        task_counts = {}
        for s in TaskStatus:
            task_counts[s.value] = sum(1 for t in tasks if t.status == s)

        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED_SUCCESS]
        total_reward = sum(t.reward_funds_cents for t in completed_tasks)

        # ----- Prestige (current snapshot) -----
        prestige_rows = db.query(CompanyPrestige).filter(
            CompanyPrestige.company_id == company_id
        ).all()
        prestige = {
            (p.domain.value if hasattr(p.domain, "value") else str(p.domain)): float(p.prestige_level)
            for p in prestige_rows
        }

        # ----- Prestige time series -----
        all_domains = sorted(prestige.keys())
        completed_ordered = (
            db.query(Task)
            .filter(
                Task.company_id == company_id,
                Task.completed_at.isnot(None),
                Task.status.in_([TaskStatus.COMPLETED_SUCCESS, TaskStatus.COMPLETED_FAIL]),
            )
            .order_by(Task.completed_at)
            .all()
        )

        task_domain_map = {}
        for t in completed_ordered:
            reqs = db.query(TaskRequirement).filter(TaskRequirement.task_id == t.id).all()
            task_domain_map[str(t.id)] = [
                r.domain.value if hasattr(r.domain, "value") else str(r.domain)
                for r in reqs
            ]

        domain_levels = {d: wc.initial_prestige_level for d in all_domains}
        last_event_time = None
        prestige_series = {d: {"times": [], "levels": []} for d in all_domains}

        if completed_ordered:
            first_time = completed_ordered[0].completed_at
            for domain in all_domains:
                prestige_series[domain]["times"].append(first_time)
                prestige_series[domain]["levels"].append(round(domain_levels[domain], 4))
            last_event_time = first_time

        for t in completed_ordered:
            if last_event_time and t.completed_at > last_event_time:
                days = (t.completed_at - last_event_time).total_seconds() / 86400
                decay = wc.prestige_decay_per_day * days
                for d in all_domains:
                    domain_levels[d] = max(wc.prestige_min, domain_levels[d] - decay)

            domains = task_domain_map.get(str(t.id), [])
            delta = float(t.reward_prestige_delta) if t.reward_prestige_delta else 0.0
            is_success = (t.status == TaskStatus.COMPLETED_SUCCESS)
            for domain in domains:
                if is_success:
                    domain_levels[domain] = min(wc.prestige_max, domain_levels[domain] + delta)
                else:
                    penalty = wc.penalty_fail_multiplier * delta
                    domain_levels[domain] = max(wc.prestige_min, domain_levels[domain] - penalty)
                prestige_series[domain]["times"].append(t.completed_at)
                prestige_series[domain]["levels"].append(round(domain_levels[domain], 4))
            last_event_time = t.completed_at

        # ----- Trust (current snapshot) -----
        trust_rows = (
            db.query(ClientTrust, Client.name, Client.tier)
            .join(Client, Client.id == ClientTrust.client_id)
            .filter(ClientTrust.company_id == company_id)
            .order_by(Client.name)
            .all()
        )
        trusts = [
            {"client": name, "trust": float(ct.trust_level), "tier": tier}
            for ct, name, tier in trust_rows
        ]
        client_names = {str(ct.client_id): name for ct, name, _ in trust_rows}
        client_tiers = {str(ct.client_id): tier for ct, _, tier in trust_rows}

        # ----- Trust time series -----
        client_tasks = (
            db.query(Task)
            .filter(
                Task.company_id == company_id,
                Task.client_id.isnot(None),
                Task.completed_at.isnot(None),
                Task.status.in_([TaskStatus.COMPLETED_SUCCESS, TaskStatus.COMPLETED_FAIL]),
            )
            .order_by(Task.completed_at)
            .all()
        )

        trust_levels = {str(ct.client_id): 0.0 for ct, _, _ in trust_rows}
        last_trust_time = None
        trust_series = {name: {"times": [], "levels": []} for name in client_names.values()}

        if client_tasks:
            first_time = client_tasks[0].completed_at
            for cid, name in client_names.items():
                trust_series[name]["times"].append(first_time)
                trust_series[name]["levels"].append(0.0)
            last_trust_time = first_time

        for t in client_tasks:
            cid = str(t.client_id)
            if cid not in trust_levels:
                continue

            if last_trust_time and t.completed_at > last_trust_time:
                days_elapsed = (t.completed_at - last_trust_time).total_seconds() / 86400
                decay = wc.trust_decay_per_day * days_elapsed
                for k in trust_levels:
                    trust_levels[k] = max(wc.trust_min, trust_levels[k] - decay)

            if t.status == TaskStatus.COMPLETED_SUCCESS:
                ratio = trust_levels[cid] / wc.trust_max
                gain = wc.trust_gain_base * ((1 - ratio) ** wc.trust_gain_diminishing_power)
                trust_levels[cid] = min(wc.trust_max, trust_levels[cid] + gain)
            else:
                trust_levels[cid] = max(wc.trust_min, trust_levels[cid] - wc.trust_fail_penalty)

            name = client_names[cid]
            trust_series[name]["times"].append(t.completed_at)
            trust_series[name]["levels"].append(round(trust_levels[cid], 4))
            last_trust_time = t.completed_at

        # Employees
        emp_count = db.query(Employee).filter(Employee.company_id == company_id).count()

        # Monthly payroll
        total_payroll = sum(
            e.salary_cents for e in db.query(Employee).filter(Employee.company_id == company_id).all()
        )

        return {
            "sim_time": sim.sim_time,
            "funds_cents": company.funds_cents,
            "funds_times": funds_times,
            "funds_vals": funds_vals,
            "task_counts": task_counts,
            "total_reward": total_reward,
            "completed": task_counts.get("completed_success", 0),
            "failed": task_counts.get("completed_fail", 0),
            "active": task_counts.get("active", 0),
            "planned": task_counts.get("planned", 0),
            "prestige": prestige,
            "prestige_series": prestige_series,
            "trusts": trusts,
            "trust_series": trust_series,
            "client_names": client_names,
            "client_tiers": client_tiers,
            "emp_count": emp_count,
            "monthly_payroll": total_payroll,
        }


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

# Header
st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
    <span style="font-size: 1.6rem; font-weight: 700; color: #e0e0e0;">YC-Bench</span>
    <span style="background: #00d4aa22; color: #00d4aa; padding: 2px 10px; border-radius: 20px;
                 font-size: 0.75rem; font-weight: 600;">LIVE</span>
</div>
""", unsafe_allow_html=True)
baseline_label = f' &nbsp;|&nbsp; baseline: <span style="color:#ff4b6e">{baseline_db.name}</span>' if baseline_db else ""
st.markdown(f'<div class="db-path">{db_file}{baseline_label}</div>', unsafe_allow_html=True)

state = query_state()
if state is None:
    st.warning("No simulation found in DB.")
    st.stop()

# Top metric cards
funds = state["funds_cents"] / 100
funds_color = "green" if funds > 0 else "red"
runway = round(funds / (state["monthly_payroll"] / 100), 1) if state["monthly_payroll"] > 0 else float("inf")

cols = st.columns(6)
metrics = [
    ("Funds", f"${funds:,.0f}", funds_color),
    ("Sim Date", state["sim_time"].strftime("%b %d, %Y"), "blue"),
    ("Completed", str(state["completed"]), "green"),
    ("Failed", str(state["failed"]), "red" if state["failed"] > 0 else "yellow"),
    ("Active", str(state["active"]), "purple"),
    ("Runway", f"{runway:.0f}mo" if runway != float("inf") else "N/A", "yellow"),
]

for col, (label, value, color) in zip(cols, metrics):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {color}">{value}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Funds chart
# ---------------------------------------------------------------------------

if state["funds_times"]:
    st.markdown('<div class="section-header">Funds Over Time</div>', unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=state["funds_times"], y=state["funds_vals"],
        mode="lines", name="LLM Agent",
        line=dict(color=ACCENT_GREEN, width=2),
        fill="tozeroy", fillcolor="rgba(0,212,170,0.08)",
    ))
    # Overlay greedy baseline if available
    if baseline_factory is not None:
        bl_times, bl_vals = query_funds_only(baseline_factory)
        if bl_times:
            fig.add_trace(go.Scatter(
                x=bl_times, y=bl_vals,
                mode="lines", name="Greedy Bot",
                line=dict(color=ACCENT_RED, width=2, dash="dot"),
            ))
            # Mark bankruptcy point
            if bl_vals[-1] < 0:
                fig.add_trace(go.Scatter(
                    x=[bl_times[-1]], y=[bl_vals[-1]],
                    mode="markers+text", name="Bankrupt",
                    marker=dict(color=ACCENT_RED, size=10, symbol="x"),
                    text=["BANKRUPT"], textposition="top center",
                    textfont=dict(color=ACCENT_RED, size=10),
                    showlegend=False,
                ))
    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color=ACCENT_RED, opacity=0.3)
    show_legend = baseline_factory is not None
    fig.update_layout(**_chart_layout(yaxis_title="USD ($)", show_legend=show_legend))
    fig.update_yaxes(tickprefix="$", tickformat=",")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Prestige & Trust side by side
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="section-header">Prestige by Domain</div>', unsafe_allow_html=True)

    has_series = any(len(s["times"]) > 0 for s in state["prestige_series"].values())
    if has_series:
        fig = go.Figure()
        for i, (domain, series) in enumerate(sorted(state["prestige_series"].items())):
            if not series["times"]:
                continue
            fig.add_trace(go.Scatter(
                x=series["times"], y=series["levels"],
                mode="lines+markers", name=domain.replace("_", " ").title(),
                line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=2),
                marker=dict(size=3),
            ))
        layout = _chart_layout(yaxis_title="Prestige Level", height=350)
        layout["yaxis"]["range"] = [0.5, 10.5]
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    elif state["prestige"]:
        domains = sorted(state["prestige"].keys())
        levels = [state["prestige"][d] for d in domains]
        labels = [d.replace("_", " ").title() for d in domains]
        fig = go.Figure(go.Bar(
            x=labels, y=levels,
            marker_color=[CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(domains))],
            marker_line=dict(width=0),
        ))
        layout = _chart_layout(yaxis_title="Level", height=350, show_legend=False)
        layout["yaxis"]["range"] = [0, 10.5]
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_right:
    st.markdown('<div class="section-header">Client Trust</div>', unsafe_allow_html=True)

    has_trust_series = any(len(s["times"]) > 0 for s in state["trust_series"].values())
    if has_trust_series:
        fig = go.Figure()
        # Sort clients by final trust level (highest first)
        sorted_clients = sorted(
            state["trust_series"].items(),
            key=lambda x: x[1]["levels"][-1] if x[1]["levels"] else 0,
            reverse=True,
        )
        for i, (client, series) in enumerate(sorted_clients):
            if not series["times"]:
                continue
            tier = None
            for cid, name in state["client_names"].items():
                if name == client:
                    tier = state["client_tiers"].get(cid)
                    break
            label = f"{client} [{tier}]" if tier else client
            fig.add_trace(go.Scatter(
                x=series["times"], y=series["levels"],
                mode="lines", name=label,
                line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=2),
            ))
        layout = _chart_layout(yaxis_title="Trust Level", height=350)
        layout["yaxis"]["range"] = [-0.2, 5.5]
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    elif state["trusts"]:
        df_t = pd.DataFrame(state["trusts"])
        df_t["label"] = df_t.apply(lambda r: f"{r['client']} [{r['tier']}]", axis=1)
        df_t = df_t.sort_values("trust", ascending=True)
        fig = go.Figure(go.Bar(
            x=df_t["trust"], y=df_t["label"],
            orientation="h",
            marker_color=ACCENT_BLUE,
            marker_line=dict(width=0),
        ))
        layout = _chart_layout(height=350, show_legend=False)
        layout["xaxis"]["range"] = [0, 5.5]
        layout["xaxis"]["title"] = "Trust Level"
        layout["margin"]["l"] = 140
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Current trust snapshot (horizontal bar)
# ---------------------------------------------------------------------------

if state["trusts"]:
    st.markdown('<div class="section-header">Current Trust Snapshot</div>', unsafe_allow_html=True)
    df_t = pd.DataFrame(state["trusts"])
    df_t["label"] = df_t.apply(lambda r: f"{r['client']} [{r['tier']}]", axis=1)
    df_t = df_t.sort_values("trust", ascending=True)

    colors = []
    for _, row in df_t.iterrows():
        t = row["trust"]
        if t >= 3.0:
            colors.append(ACCENT_GREEN)
        elif t >= 1.0:
            colors.append(ACCENT_BLUE)
        elif t > 0:
            colors.append(ACCENT_YELLOW)
        else:
            colors.append(GRID_COLOR)

    fig = go.Figure(go.Bar(
        x=df_t["trust"], y=df_t["label"],
        orientation="h",
        marker_color=colors,
        marker_line=dict(width=0),
        text=[f"{t:.2f}" for t in df_t["trust"]],
        textposition="outside",
        textfont=dict(size=11, color=TEXT_MUTED),
    ))
    layout = _chart_layout(height=max(200, len(df_t) * 35 + 60), show_legend=False)
    layout["xaxis"]["range"] = [0, 5.5]
    layout["xaxis"]["title"] = "Trust Level"
    layout["margin"]["l"] = 160
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Auto-refresh
# ---------------------------------------------------------------------------

st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
col_r1, col_r2 = st.columns([3, 1])
with col_r2:
    auto = st.toggle("Auto-refresh", value=True)
if auto:
    time.sleep(5)
    st.rerun()
