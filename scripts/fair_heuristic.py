"""Fair heuristic that runs through the same CLI as LLMs, with turn counting."""
import json, os, subprocess, sys
from pathlib import Path

sys.path.insert(0, "src")
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1

DB_PATH = f"db/fair_heuristic_medium_{seed}.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["YC_BENCH_EXPERIMENT"] = "medium"
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"

from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from yc_bench.config import load_config
from yc_bench.db.session import build_engine, build_session_factory, session_scope
from yc_bench.db.base import Base
from yc_bench.services.seed_world import seed_world, SeedWorldRequest
from yc_bench.db.models.sim_state import SimState

exp = load_config("medium")
cfg = exp.world
engine = build_engine(f"sqlite:///{DB_PATH}")
Base.metadata.create_all(engine)
factory = build_session_factory(engine)
start = datetime(2025, 1, 1, tzinfo=timezone.utc)
with session_scope(factory) as db:
    result = seed_world(db, SeedWorldRequest(
        run_seed=seed, company_name="BenchCo", horizon_years=1,
        employee_count=cfg.num_employees, market_task_count=cfg.num_market_tasks,
        cfg=cfg, start_date=start,
    ))
    db.add(SimState(company_id=result.company_id, sim_time=start,
        horizon_end=start + relativedelta(years=1), run_seed=seed, replenish_counter=0))
    db.flush()

def cmd(c):
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
    env["YC_BENCH_EXPERIMENT"] = "medium"
    r = subprocess.run(["uv", "run"] + f"yc-bench {c}".split(),
        capture_output=True, text=True, env=env, cwd=".")
    try: return json.loads(r.stdout)
    except: return {"raw": r.stdout + r.stderr}

AUTO_ADVANCE = 5
turns_since_resume = 0

def tick():
    """Count a turn. Auto-advance if needed."""
    global turns_since_resume
    turns_since_resume += 1
    if turns_since_resume >= AUTO_ADVANCE:
        result = cmd("sim resume")
        turns_since_resume = 0
        return result
    return None

# Get employee skills once (1 turn)
emps = cmd("employee list")
tick()
emp_skills = {}
for e in emps.get("employees", []):
    emp_skills[e["name"]] = e.get("skill_rates", {})

avoid = set()
context_window = []  # simulate 20-turn context truncation

while True:
    # Browse (1 turn)
    market = cmd("market browse --limit 10")
    auto = tick()
    if auto and (auto.get("horizon_reached") or auto.get("bankrupt")):
        break

    tasks = market.get("tasks", [])
    if not tasks:
        result = cmd("sim resume")
        turns_since_resume = 0
        if result.get("horizon_reached") or result.get("bankrupt"):
            break
        continue

    # Filter avoided clients
    candidates = [t for t in tasks if t.get("client_name", "") not in avoid]
    if not candidates:
        candidates = tasks[:1]

    # Inspect top task by reward (1 turn)
    tid = candidates[0]["task_id"]
    info = cmd(f"task inspect --task-id {tid}")
    auto = tick()
    if auto and (auto.get("horizon_reached") or auto.get("bankrupt")):
        break

    reqs = info.get("requirements", [])
    if reqs:
        domain = reqs[0].get("domain", "research")
    else:
        domain = "research"

    # Assign top 4 by domain
    rates = [(name, skills.get(domain, 0)) for name, skills in emp_skills.items()]
    rates.sort(key=lambda x: -x[1])
    top4 = ",".join(r[0] for r in rates[:4])

    # Accept (1 turn)
    cmd(f"task accept --task-id {tid}")
    auto = tick()
    if auto and (auto.get("horizon_reached") or auto.get("bankrupt")):
        break

    # Assign + dispatch (1 turn each)
    cmd(f"task assign --task-id {tid} --employees {top4}")
    auto = tick()
    if auto and (auto.get("horizon_reached") or auto.get("bankrupt")):
        break

    cmd(f"task dispatch --task-id {tid}")
    auto = tick()  # this is turn 5 → auto-advance!
    if auto and (auto.get("horizon_reached") or auto.get("bankrupt")):
        break

    # If auto-advance didn't trigger (shouldn't happen at turn 5), manually resume
    if turns_since_resume > 0:
        result = cmd("sim resume")
        turns_since_resume = 0
        if result.get("horizon_reached") or result.get("bankrupt"):
            break

        # Learn from failures
        for ev in result.get("wake_events", []):
            if ev.get("type") == "task_completed" and not ev.get("success"):
                client = ev.get("client_name", "")
                history = cmd("client history")
                tick()
                for ch in history.get("client_history", []):
                    if ch["client_name"] == client and ch["tasks_failed"] >= 2:
                        avoid.add(client)

# Final
status = cmd("company status")
funds = status.get("funds_cents", 0) / 100
history = cmd("client history")
ok = sum(ch["tasks_succeeded"] for ch in history.get("client_history", []))
fail = sum(ch["tasks_failed"] for ch in history.get("client_history", []))
print(f"Seed {seed}: ${funds:,.0f} | ok={ok} fail={fail} | avoiding={avoid or 'none'}")
