"""Streamlit dashboard — watch YC-Bench runs funds over time.

Usage:
    uv run streamlit run scripts/watch_dashboard.py
"""
from __future__ import annotations

import re
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import streamlit as st
import plotly.graph_objects as go

DB_DIR = Path("db")
REFRESH_SECS = 10

MODEL_COLORS = {
    "gpt-5.4": "#4da6ff",
    "gpt-5.4-mini": "#ffd43b",
    "gpt-5.4-nano": "#ff8c42",
    "gemini-3.1-pro-preview": "#22cc44",
    "gemini-3-flash-preview": "#b197fc",
    "claude-sonnet-4-6": "#ff69b4",
}

st.set_page_config(page_title="YC-Bench", layout="wide", page_icon="📊")
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
</style>
""", unsafe_allow_html=True)


def _model_color(label: str) -> str:
    for key, color in MODEL_COLORS.items():
        if key in label:
            return color
    return "#8b8d93"


def _parse_db_stem(stem: str) -> tuple[str, int, str]:
    parts = stem.split("_", 2)
    if len(parts) < 3:
        return stem, 0, stem
    try:
        seed = int(parts[1])
    except ValueError:
        return stem, 0, stem
    label = re.sub(r"^(openai|gemini|anthropic)_", "", parts[2])
    return parts[0], seed, label


def _read_funds_series(db_path: Path) -> dict | None:
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute("SELECT sim_time, horizon_end FROM sim_state LIMIT 1").fetchone()
        co = conn.execute("SELECT funds_cents FROM companies LIMIT 1").fetchone()
        if not row or not co:
            return None
        ok = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='completed_success'").fetchone()[0]
        fail = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='completed_fail'").fetchone()[0]
        ledger = conn.execute(
            "SELECT occurred_at, amount_cents FROM ledger_entries ORDER BY occurred_at"
        ).fetchall()
        running = 20_000_000
        funds_by_day = {}
        for occ, amt in ledger:
            running += amt
            funds_by_day[occ[:10]] = running
        return {
            "sim_time": row[0][:10],
            "funds": co[0] / 100,
            "ok": ok, "fail": fail,
            "done": row[0] >= row[1] or co[0] < 0,
            "bankrupt": co[0] < 0,
            "funds_by_day": {k: v / 100 for k, v in funds_by_day.items()},
        }
    except Exception:
        return None
    finally:
        conn.close()


st.markdown("""
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
    <span style="font-size: 1.6rem; font-weight: 700; color: #e0e0e0;">YC-Bench</span>
    <span style="background: #00d4aa22; color: #00d4aa; padding: 2px 10px; border-radius: 20px;
                 font-size: 0.75rem; font-weight: 600;">LIVE</span>
</div>
""", unsafe_allow_html=True)

average_mode = st.toggle("Average across seeds", value=False)

placeholder = st.empty()

while True:
    with placeholder.container():
        dbs = sorted(DB_DIR.glob("*.db"))
        if not dbs:
            st.warning("No DB files in db/")
            time.sleep(REFRESH_SECS)
            continue

        model_runs = defaultdict(list)
        for p in dbs:
            config, seed, label = _parse_db_stem(p.stem)
            data = _read_funds_series(p)
            if data:
                model_runs[label].append((seed, data))

        if not average_mode:
            # --- Per-seed curves ---
            fig = go.Figure()
            for label in sorted(model_runs.keys()):
                color = _model_color(label)
                for seed, data in sorted(model_runs[label]):
                    fbd = data.get("funds_by_day", {})
                    if not fbd:
                        continue
                    days = sorted(fbd.keys())
                    vals = [fbd[d] for d in days]
                    trace_name = f"{label} (seed {seed})"
                    status = ""
                    if data["done"]:
                        status = f" — ${data['funds']:,.0f}"
                        if data["bankrupt"]:
                            status += " BANKRUPT"
                    fig.add_trace(go.Scatter(
                        x=days, y=vals, mode="lines",
                        name=trace_name + status,
                        line=dict(color=color, width=2, dash="dot" if seed > 1 else "solid"),
                        hovertemplate=f"<b>{trace_name}</b><br>%{{x}}<br>${{y:,.0f}}<extra></extra>",
                    ))
        else:
            # --- Averaged curves ---
            fig = go.Figure()
            for label in sorted(model_runs.keys()):
                color = _model_color(label)
                all_days = set()
                series = []
                for seed, data in model_runs[label]:
                    fbd = data.get("funds_by_day", {})
                    if fbd:
                        all_days.update(fbd.keys())
                        series.append(fbd)
                if not all_days or not series:
                    continue
                common_days = sorted(all_days)
                aligned = []
                for s in series:
                    s_days = sorted(s.keys())
                    if not s_days:
                        continue
                    vals, last_val, si = [], 200_000, 0
                    for d in common_days:
                        while si < len(s_days) and s_days[si] <= d:
                            last_val = s[s_days[si]]
                            si += 1
                        vals.append(last_val)
                    aligned.append(vals)
                if not aligned:
                    continue
                arr = np.array(aligned)
                mean = arr.mean(axis=0)
                trace_name = f"{label} (n={len(aligned)})"
                fig.add_trace(go.Scatter(
                    x=common_days, y=mean, mode="lines",
                    name=trace_name,
                    line=dict(color=color, width=3),
                    hovertemplate=f"<b>{trace_name}</b><br>%{{x}}<br>${{y:,.0f}}<extra></extra>",
                ))
                if len(aligned) > 1:
                    lo, hi = arr.min(axis=0), arr.max(axis=0)
                    _r, _g, _b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                    fig.add_trace(go.Scatter(
                        x=list(common_days) + list(common_days)[::-1],
                        y=list(hi) + list(lo[::-1]),
                        fill="toself", fillcolor=f"rgba({_r},{_g},{_b},0.1)",
                        line=dict(color="rgba(0,0,0,0)"),
                        showlegend=False, hoverinfo="skip",
                    ))

        fig.add_hline(y=200_000, line_dash="dash", line_color="#555",
                      annotation_text="Starting $200K")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            height=600,
            margin=dict(l=60, r=20, t=40, b=40),
            xaxis=dict(gridcolor="#2a2d35", tickfont=dict(size=10, color="#8b8d93")),
            yaxis=dict(title="Funds ($)", gridcolor="#2a2d35", tickprefix="$", tickformat=",",
                       tickfont=dict(size=10, color="#8b8d93")),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#e0e0e0"),
                        orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
            hovermode="closest",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"funds_{time.time()}")
        st.caption(f"Refreshing every {REFRESH_SECS}s — {time.strftime('%H:%M:%S')}")

    time.sleep(REFRESH_SECS)
