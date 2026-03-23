"""Optimal heuristic — plays YC-Bench using direct Python calls (no subprocess).

Reads structured data (domain, qty) from DB objects directly.
No turn limits, no context truncation, perfect memory.

Usage:
    uv run python scripts/optimal_heuristic.py --seed 1 --config medium
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dateutil.relativedelta import relativedelta
from sqlalchemy import func

from yc_bench.config import load_config
from yc_bench.db.base import Base
from yc_bench.db.models.client import Client, ClientTrust
from yc_bench.db.models.company import Company, CompanyPrestige
from yc_bench.db.models.employee import Employee, EmployeeSkillRate
from yc_bench.db.models.sim_state import SimState
from yc_bench.db.models.task import Task, TaskAssignment, TaskRequirement, TaskStatus
from yc_bench.db.session import build_engine, build_session_factory, session_scope
from yc_bench.services.seed_world import seed_world, SeedWorldRequest
from yc_bench.core.engine import advance_time, fetch_next_event
from yc_bench.core.eta import recalculate_etas


def _compute_deadline_simple(accepted_at, max_qty, cfg):
    """Simplified deadline computation."""
    from yc_bench.core.business_time import add_business_hours
    work_hours = cfg.workday_end_hour - cfg.workday_start_hour
    biz_days = max(cfg.deadline_min_biz_days, int(max_qty / cfg.deadline_qty_per_day))
    return add_business_hours(accepted_at, Decimal(str(biz_days)) * Decimal(str(work_hours)))


def run(seed: int, config: str):
    db_path = f"db/optimal_heuristic_{config}_{seed}.db"
    db_url = f"sqlite:///{db_path}"

    if Path(db_path).exists():
        Path(db_path).unlink()

    os.environ["YC_BENCH_EXPERIMENT"] = config
    os.environ["DATABASE_URL"] = db_url

    exp = load_config(config)
    cfg = exp.world

    engine = build_engine(db_url)
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)

    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with session_scope(factory) as db:
        result = seed_world(db, SeedWorldRequest(
            run_seed=seed, company_name="BenchCo", horizon_years=1,
            employee_count=cfg.num_employees, market_task_count=cfg.num_market_tasks,
            cfg=cfg, start_date=start,
        ))
        company_id = result.company_id
        db.add(SimState(
            company_id=company_id, sim_time=start,
            horizon_end=start + relativedelta(years=1),
            run_seed=seed, replenish_counter=0,
        ))
        db.flush()

    avoid_clients = set()

    with session_scope(factory) as db:
        # Cache employee skills
        emp_skills = {}
        for emp in db.query(Employee).filter(Employee.company_id == company_id).all():
            rates = {}
            for r in db.query(EmployeeSkillRate).filter(EmployeeSkillRate.employee_id == emp.id).all():
                rates[r.domain.value] = float(r.rate_domain_per_hour)
            emp_skills[emp.id] = rates

        while True:
            sim_state = db.query(SimState).filter(SimState.company_id == company_id).one()
            company = db.query(Company).filter(Company.id == company_id).one()

            if company.funds_cents < 0 or sim_state.sim_time >= sim_state.horizon_end:
                break

            # Get prestige and trust maps
            prestige_map = {
                p.domain: float(p.prestige_level)
                for p in db.query(CompanyPrestige).filter(CompanyPrestige.company_id == company_id).all()
            }
            trust_map = {
                str(ct.client_id): float(ct.trust_level)
                for ct in db.query(ClientTrust).filter(ClientTrust.company_id == company_id).all()
            }

            # Browse top 50 by reward
            market_tasks = (
                db.query(Task)
                .filter(Task.status == TaskStatus.MARKET)
                .order_by(Task.reward_funds_cents.desc())
                .limit(50)
                .all()
            )

            picked = []
            for task in market_tasks:
                if len(picked) >= 2:
                    break
                # Avoid bad clients
                if task.client_id:
                    client = db.query(Client).filter(Client.id == task.client_id).one_or_none()
                    if client and client.name in avoid_clients:
                        continue
                # Check prestige
                reqs = db.query(TaskRequirement).filter(TaskRequirement.task_id == task.id).all()
                if not all(prestige_map.get(r.domain, 1) >= task.required_prestige for r in reqs):
                    continue
                # Check trust
                if task.required_trust > 0 and task.client_id:
                    if trust_map.get(str(task.client_id), 0) < task.required_trust:
                        continue
                picked.append((task, reqs))

            if not picked:
                event = fetch_next_event(db, company_id, sim_state.horizon_end)
                if event is None:
                    break
                adv = advance_time(db, company_id, event.scheduled_at)
                if adv.bankrupt or adv.horizon_reached:
                    break
                continue

            for task, reqs in picked:
                domain = reqs[0].domain.value if reqs else "research"
                trust_level = trust_map.get(str(task.client_id), 0) if task.client_id else 0

                # Check RAT
                is_rat = False
                client_row = db.query(Client).filter(Client.id == task.client_id).one_or_none() if task.client_id else None
                if client_row and client_row.loyalty < -0.3:
                    is_rat = True

                # Trust work reduction (non-RAT only)
                if not is_rat:
                    work_reduction = cfg.trust_work_reduction_max * (trust_level / cfg.trust_max)
                    for r in reqs:
                        reduced = int(float(r.required_qty) * (1 - work_reduction))
                        r.required_qty = max(200, reduced)

                max_qty = max(float(r.required_qty) for r in reqs)
                deadline = _compute_deadline_simple(sim_state.sim_time, max_qty, cfg)

                task.advertised_reward_cents = task.reward_funds_cents

                # Scope creep
                if is_rat:
                    intensity = abs(client_row.loyalty)
                    inflation = max(1.3, cfg.scope_creep_max * intensity)
                    for r in reqs:
                        inflated = float(r.required_qty) * (1 + inflation)
                        r.required_qty = int(min(25000, max(200, inflated)))

                task.status = TaskStatus.PLANNED
                task.company_id = company_id
                task.accepted_at = sim_state.sim_time
                task.deadline = deadline

                # Replacement task
                from yc_bench.services.generate_tasks import generate_replacement_task
                counter = sim_state.replenish_counter
                sim_state.replenish_counter = counter + 1

                replaced_client_index = 0
                if task.client_id:
                    for i, c in enumerate(db.query(Client).order_by(Client.name).all()):
                        if c.id == task.client_id:
                            replaced_client_index = i
                            break
                spec_domains = None
                if client_row:
                    spec_domains = client_row.specialty_domains

                rep = generate_replacement_task(
                    run_seed=sim_state.run_seed, replenish_counter=counter,
                    replaced_prestige=task.required_prestige,
                    replaced_client_index=replaced_client_index,
                    cfg=cfg, specialty_domains=spec_domains,
                )
                clients_list = db.query(Client).order_by(Client.name).all()
                rep_client = clients_list[rep.client_index % len(clients_list)] if clients_list else None
                rep_row = Task(
                    id=uuid4(), company_id=None,
                    client_id=rep_client.id if rep_client else None,
                    status=TaskStatus.MARKET, title=rep.title,
                    required_prestige=rep.required_prestige,
                    reward_funds_cents=rep.reward_funds_cents,
                    reward_prestige_delta=rep.reward_prestige_delta,
                    skill_boost_pct=rep.skill_boost_pct,
                    required_trust=rep.required_trust,
                )
                db.add(rep_row)
                for dom, qty in rep.requirements.items():
                    db.add(TaskRequirement(task_id=rep_row.id, domain=dom, required_qty=qty, completed_qty=0))

                # Assign top 4 by domain
                rated = sorted(emp_skills.items(), key=lambda x: -x[1].get(domain, 0))
                for eid, _ in rated[:4]:
                    db.add(TaskAssignment(task_id=task.id, employee_id=eid, assigned_at=sim_state.sim_time))

                task.status = TaskStatus.ACTIVE
                recalculate_etas(db, company_id, sim_state.sim_time, impacted_task_ids={task.id}, milestones=cfg.task_progress_milestones)

            db.flush()

            # Advance time
            event = fetch_next_event(db, company_id, sim_state.horizon_end)
            if event is None:
                break
            adv = advance_time(db, company_id, event.scheduled_at)

            # Learn from failures
            completed = db.query(Task).filter(
                Task.company_id == company_id,
                Task.success == False,
            ).all()
            for t in completed:
                if t.client_id:
                    fail_count = db.query(func.count(Task.id)).filter(
                        Task.client_id == t.client_id,
                        Task.company_id == company_id,
                        Task.success == False,
                    ).scalar() or 0
                    if fail_count >= 2:
                        c = db.query(Client).filter(Client.id == t.client_id).one_or_none()
                        if c:
                            avoid_clients.add(c.name)

            if adv.bankrupt or adv.horizon_reached:
                break

        # Final
        company = db.query(Company).filter(Company.id == company_id).one()
        ok = db.query(func.count(Task.id)).filter(
            Task.company_id == company_id, Task.status == TaskStatus.COMPLETED_SUCCESS
        ).scalar() or 0
        fail = db.query(func.count(Task.id)).filter(
            Task.company_id == company_id, Task.status == TaskStatus.COMPLETED_FAIL
        ).scalar() or 0
        print(f"Seed {seed}: ${company.funds_cents / 100:,.0f} | ok={ok} fail={fail} | avoiding={avoid_clients or 'none'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--config", default="medium")
    args = parser.parse_args()
    t0 = time.time()
    run(args.seed, args.config)
    print(f"Time: {time.time() - t0:.1f}s")
