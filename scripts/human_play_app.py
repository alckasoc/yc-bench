"""Streamlit app for playing YC-Bench as a human — same conditions as LLM.

Usage:
    uv run streamlit run scripts/human_play_app.py -- --seed 1 --config medium
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from yc_bench.agent.prompt import SYSTEM_PROMPT, build_turn_context

st.set_page_config(page_title="YC-Bench Play", layout="wide", page_icon="🎮")

HISTORY_WINDOW = 20
AUTO_ADVANCE_TURNS = 5

# Parse args
args = sys.argv[1:]
seed = 1
config = "medium"
for i, a in enumerate(args):
    if a == "--seed" and i + 1 < len(args):
        seed = int(args[i + 1])
    if a == "--config" and i + 1 < len(args):
        config = args[i + 1]

DB_PATH = f"db/human_play_{config}_{seed}.db"
DB_URL = f"sqlite:///{DB_PATH}"

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.turn = 0
    st.session_state.turns_since_resume = 0
    st.session_state.history = []  # list of (turn, cmd, output)
    st.session_state.last_events = None
    st.session_state.game_over = False
    st.session_state.game_over_msg = ""


def init_game():
    if Path(DB_PATH).exists():
        Path(DB_PATH).unlink()
    os.environ["YC_BENCH_EXPERIMENT"] = config
    os.environ["DATABASE_URL"] = DB_URL
    from yc_bench.config import load_config
    from yc_bench.db.session import build_engine, build_session_factory, session_scope
    from yc_bench.db.base import Base
    from yc_bench.services.seed_world import seed_world, SeedWorldRequest
    from yc_bench.db.models.sim_state import SimState
    from dateutil.relativedelta import relativedelta
    exp = load_config(config)
    cfg = exp.world
    engine = build_engine(DB_URL)
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with session_scope(factory) as db:
        result = seed_world(db, SeedWorldRequest(
            run_seed=seed, company_name="BenchCo", horizon_years=1,
            employee_count=cfg.num_employees, market_task_count=cfg.num_market_tasks,
            cfg=cfg, start_date=start,
        ))
        db.add(SimState(
            company_id=result.company_id, sim_time=start,
            horizon_end=start + relativedelta(years=1),
            run_seed=seed, replenish_counter=0,
        ))
        db.flush()
    st.session_state.initialized = True


def run_cmd(cmd: str) -> str:
    env = os.environ.copy()
    env["DATABASE_URL"] = DB_URL
    env["YC_BENCH_EXPERIMENT"] = config
    full_cmd = cmd if cmd.startswith("yc-bench") else f"yc-bench {cmd}"
    result = subprocess.run(
        ["uv", "run"] + full_cmd.split(),
        capture_output=True, text=True, env=env,
        cwd=str(Path(__file__).parent.parent),
    )
    return result.stdout.strip() or result.stderr.strip()


def parse_json(output: str):
    try:
        return json.loads(output)
    except Exception:
        return None


if not st.session_state.initialized:
    init_game()

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.markdown("# 🎮 YC-Bench")

if st.session_state.game_over:
    st.error(f"GAME OVER: {st.session_state.game_over_msg}")
    st.code(run_cmd("company status"), language="json")
    st.stop()

# Two-column layout: system prompt on left, game on right
left, right = st.columns([2, 1])

with left:
    st.markdown("### System Prompt")
    st.markdown(SYSTEM_PROMPT, unsafe_allow_html=False)

with right:
    # Turn context (same as LLM)
    status = parse_json(run_cmd("company status")) or {}
    funds = status.get("funds_cents", 0)
    ctx = build_turn_context(
        turn_number=st.session_state.turn + 1,
        sim_time=status.get("sim_time", "?"),
        horizon_end=status.get("horizon_end", "?"),
        funds_cents=funds,
        active_tasks=status.get("tasks", {}).get("active", 0),
        planned_tasks=status.get("tasks", {}).get("planned", 0),
        employee_count=status.get("employee_count", 0),
        monthly_payroll_cents=status.get("monthly_payroll_cents", 0),
        bankrupt=funds < 0,
        last_wake_events=st.session_state.last_events,
    )
    st.markdown(ctx)

    st.divider()

    # Command input
    cmd = st.text_input(
        "Command",
        placeholder="e.g. market browse, employee list, task accept --task-id Task-10",
        key=f"cmd_{st.session_state.turn}",
    )

    if cmd:
        st.session_state.turn += 1
        output = run_cmd(cmd)
        st.session_state.history.append((st.session_state.turn, cmd, output))

        if "sim resume" in cmd:
            st.session_state.turns_since_resume = 0
            data = parse_json(output)
            st.session_state.last_events = data.get("events", []) if data else None
            if "bankrupt" in output.lower() or "horizon_end" in output.lower():
                st.session_state.game_over = True
                st.session_state.game_over_msg = output[:300]
        else:
            st.session_state.turns_since_resume += 1
            st.session_state.last_events = None

        # Auto-advance
        if st.session_state.turns_since_resume >= AUTO_ADVANCE_TURNS:
            auto_output = run_cmd("sim resume")
            st.session_state.history.append((st.session_state.turn, "[auto] sim resume", auto_output))
            st.session_state.turns_since_resume = 0
            data = parse_json(auto_output)
            st.session_state.last_events = data.get("events", []) if data else None
            if "bankrupt" in auto_output.lower() or "horizon_end" in auto_output.lower():
                st.session_state.game_over = True
                st.session_state.game_over_msg = auto_output[:300]
            st.warning(f"⚡ Auto-advanced (no sim resume for {AUTO_ADVANCE_TURNS} turns)")

        # Show output
        st.markdown(f"**Turn {st.session_state.turn}**: `{cmd}`")
        st.code(output, language="json")
        st.rerun()

    # History (last 20 turns)
    if st.session_state.history:
        visible = st.session_state.history[-HISTORY_WINDOW:]
        with st.expander(f"History ({len(visible)}/{len(st.session_state.history)} turns)", expanded=True):
            for t, c, out in reversed(visible):
                st.markdown(f"**Turn {t}**: `{c}`")
                st.code(out, language="json")
