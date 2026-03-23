"""Play YC-Bench as a human under the exact same conditions as an LLM agent.

Constraints (identical to LLM):
  - 5 turns without `sim resume` → auto-advance
  - Only last 20 turns of history visible (context truncation)
  - Same CLI commands, same economic rules
  - Scratchpad persists (like the LLM's system prompt injection)

Usage:
    uv run python scripts/human_play.py --seed 1 --config medium
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from yc_bench.agent.prompt import SYSTEM_PROMPT

HISTORY_WINDOW = 20
AUTO_ADVANCE_TURNS = 5


def run_cmd(cmd: str, db_path: str, config: str) -> str:
    """Execute a yc-bench CLI command and return output."""
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["YC_BENCH_EXPERIMENT"] = config
    result = subprocess.run(
        ["uv", "run"] + cmd.split(),
        capture_output=True, text=True, env=env, cwd=str(Path(__file__).parent.parent),
    )
    return result.stdout.strip() or result.stderr.strip()


def get_state(db_path: str, config: str) -> dict:
    """Get current sim state."""
    output = run_cmd("yc-bench company status", db_path, config)
    try:
        return json.loads(output)
    except Exception:
        return {"raw": output}


def setup_game(seed: int, config: str) -> str:
    """Initialize a fresh game using the same seeding as yc-bench run."""
    db_path = f"db/human_play_{config}_{seed}.db"
    if Path(db_path).exists():
        Path(db_path).unlink()

    os.environ["YC_BENCH_EXPERIMENT"] = config
    os.environ["YC_BENCH_DB"] = db_path

    from datetime import datetime, timezone
    from yc_bench.config import load_config
    from yc_bench.db.session import build_engine, build_session_factory, session_scope
    from yc_bench.db.base import Base
    from yc_bench.services.seed_world import seed_world, SeedWorldRequest
    from yc_bench.db.models.sim_state import SimState

    exp = load_config(config)
    cfg = exp.world

    engine = build_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)

    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with session_scope(factory) as db:
        result = seed_world(db, SeedWorldRequest(
            run_seed=seed,
            company_name="BenchCo",
            horizon_years=cfg.horizon_years if hasattr(cfg, 'horizon_years') else 1,
            employee_count=cfg.num_employees,
            market_task_count=cfg.num_market_tasks,
            cfg=cfg,
            start_date=start,
        ))
        # Create sim state
        from dateutil.relativedelta import relativedelta
        horizon_end = start + relativedelta(years=1)
        db.add(SimState(
            company_id=result.company_id,
            sim_time=start,
            horizon_end=horizon_end,
            run_seed=seed,
            replenish_counter=0,
        ))
        db.flush()

    return db_path


def main():
    parser = argparse.ArgumentParser(description="Play YC-Bench as a human")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--config", default="medium")
    args = parser.parse_args()

    db_path = setup_game(args.seed, args.config)

    print("\033[1;36m" + "=" * 70)
    print("  YC-BENCH — HUMAN PLAY MODE")
    print("=" * 70 + "\033[0m")
    print()
    print("\033[33mSystem prompt (identical to LLM):\033[0m")
    print()
    for line in SYSTEM_PROMPT.strip().split('\n'):
        print(f"  {line}")
    print()
    print("\033[33mRules (same as LLM):\033[0m")
    print(f"  - {AUTO_ADVANCE_TURNS} turns without 'sim resume' → auto-advance")
    print(f"  - Only last {HISTORY_WINDOW} turns of history shown (context truncation)")
    print("  - Type commands without 'yc-bench' prefix (e.g. 'market browse')")
    print("  - Type 'help' for full system prompt, 'quit' to exit")
    print()
    print()
    print("\033[33mControls:\033[0m")
    print("  Type commands without 'yc-bench' prefix (e.g. 'market browse')")
    print("  Type 'help' for the system prompt again, 'quit' to exit")
    print()

    history = []  # list of (turn, command, output)
    turn = 0
    turns_since_resume = 0
    last_events = None  # wake events from last sim resume

    while True:
        turn += 1

        # Show truncated history (last N turns)
        if history:
            visible = history[-HISTORY_WINDOW:]
            print(f"\033[90m--- History (last {len(visible)}/{len(history)} turns) ---\033[0m")
            for t, cmd, out in visible[-3:]:  # show last 3 compactly
                print(f"\033[90m  T{t}: {cmd}\033[0m")
                # Show first 2 lines of output
                lines = out.split('\n')[:2]
                for l in lines:
                    print(f"\033[90m    {l}\033[0m")

        # Show per-turn context (identical to what the LLM receives)
        turn_context = run_cmd("yc-bench company status", db_path, args.config)
        try:
            state = json.loads(turn_context)
            funds = state.get("funds_cents", 0)
            sim_time = state.get("sim_time", "?")
            horizon_end = state.get("horizon_end", "?")
            active = state.get("tasks", {}).get("active", 0)
            planned = state.get("tasks", {}).get("planned", 0)
            emp_count = state.get("employee_count", 0)
            payroll = state.get("monthly_payroll_cents", 0)
            bankrupt = funds < 0

            from yc_bench.agent.prompt import build_turn_context
            ctx = build_turn_context(
                turn_number=turn,
                sim_time=sim_time,
                horizon_end=horizon_end,
                funds_cents=funds,
                active_tasks=active,
                planned_tasks=planned,
                employee_count=emp_count,
                monthly_payroll_cents=payroll,
                bankrupt=bankrupt,
                last_wake_events=last_events,
            )
            print(f"\n\033[36m{ctx}\033[0m")
        except Exception:
            print(f"\n\033[1mTurn {turn}\033[0m | {turn_context[:200]}")

        # Check auto-advance
        if turns_since_resume >= AUTO_ADVANCE_TURNS:
            print(f"\033[33m⚡ Auto-advancing (no sim resume for {AUTO_ADVANCE_TURNS} turns)\033[0m")
            output = run_cmd("yc-bench sim resume", db_path, args.config)
            print(output[:200])
            history.append((turn, "[auto] sim resume", output))
            turns_since_resume = 0
            try:
                data = json.loads(output)
                last_events = data.get("events", []) if isinstance(data, dict) else None
            except Exception:
                last_events = None
            # Check terminal
            if "bankrupt" in output.lower() or "horizon" in output.lower():
                print("\n\033[1;31m=== GAME OVER ===\033[0m")
                print(output)
                break
            continue

        # Get player input
        try:
            raw_input = input("\033[1;37m> \033[0m").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nQuitting.")
            break

        if not raw_input:
            continue
        if raw_input.lower() == "quit":
            break
        if raw_input.lower() == "help":
            print(SYSTEM_PROMPT)
            turn -= 1  # don't count help as a turn
            continue

        # Normalize command
        cmd = raw_input
        if not cmd.startswith("yc-bench"):
            cmd = "yc-bench " + cmd

        # Execute
        output = run_cmd(cmd, db_path, args.config)
        print(output[:2000])

        history.append((turn, raw_input, output))

        # Track sim resume and capture wake events
        if "sim resume" in raw_input or "sim resume" in cmd:
            turns_since_resume = 0
            # Parse wake events from output
            try:
                data = json.loads(output)
                last_events = data.get("events", []) if isinstance(data, dict) else None
            except Exception:
                last_events = None
            # Check terminal
            if "bankrupt" in output.lower() or "horizon" in output.lower():
                print("\n\033[1;31m=== GAME OVER ===\033[0m")
                print(output)
                break
        else:
            turns_since_resume += 1
            last_events = None

    # Final stats
    print("\n\033[1;36m=== FINAL STATS ===\033[0m")
    print(run_cmd("yc-bench company status", db_path, args.config))
    print(f"\nTotal turns: {turn}")
    print(f"DB saved at: {db_path}")


if __name__ == "__main__":
    main()
