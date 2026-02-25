from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..config.sampling import sample_from_spec
from ..config.schema import WorldConfig
from ..db.models.company import Domain
from .rng import RngStreams, sample_without_replacement
from .task_catalog import pick_task_text


@dataclass(frozen=True)
class GeneratedTask:
    title: str
    description: str
    required_prestige: int
    reward_funds_cents: int
    reward_prestige_delta: float
    skill_boost_pct: float
    status: str
    company_id: Any | None
    accepted_at: datetime | None
    deadline: datetime | None
    completed_at: datetime | None
    success: bool | None
    halfway_event_emitted: bool
    requirements: dict[str, int]


# First 10 market tasks are given explicit prestige values to guarantee a
# climbable ladder from the start (avoids runs where all early tasks need
# prestige 4+ before any are completable).
_STRATIFIED_PRESTIGE = [1, 1, 1, 1, 2, 2, 2, 3, 3, 4]

_ALL_DOMAINS = list(Domain)


def _sample_required_prestige(rng, cfg, index=None):
    if index is not None and index < len(_STRATIFIED_PRESTIGE):
        return _STRATIFIED_PRESTIGE[index]
    return int(sample_from_spec(rng, cfg.dist.required_prestige))


def _sample_reward_funds_cents(rng, cfg, prestige=1):
    base = int(sample_from_spec(rng, cfg.dist.reward_funds_cents))
    # Scale reward by prestige: higher-prestige tasks pay proportionally more
    return int(base * (1 + cfg.reward_prestige_scale * (prestige - 1)))


def _sample_reward_prestige_delta(rng, cfg):
    return sample_from_spec(rng, cfg.dist.reward_prestige_delta)


def _sample_skill_boost_pct(rng, cfg):
    return sample_from_spec(rng, cfg.dist.skill_boost)


def _sample_domain_count(rng, cfg):
    return int(sample_from_spec(rng, cfg.dist.domain_count))


def _sample_required_qty(rng, cfg):
    return int(sample_from_spec(rng, cfg.dist.required_qty))


def _sample_requirements(rng, cfg):
    k = _sample_domain_count(rng, cfg)
    picked_domains = sample_without_replacement(rng, _ALL_DOMAINS, k)
    return {domain: _sample_required_qty(rng, cfg) for domain in picked_domains}


def _pick_title_desc(rng, primary_domain, serial):
    title, description = pick_task_text(rng, primary_domain)
    domain_str = primary_domain.value if hasattr(primary_domain, "value") else str(primary_domain)
    title = f"{title} [{domain_str.upper()}-{serial}]"
    return title, description


def _make_task(rng, cfg, prestige, serial, requirements):
    title, description = _pick_title_desc(rng, next(iter(requirements)), serial)
    return GeneratedTask(
        title=title,
        description=description,
        required_prestige=prestige,
        reward_funds_cents=_sample_reward_funds_cents(rng, cfg, prestige=prestige),
        reward_prestige_delta=_sample_reward_prestige_delta(rng, cfg),
        skill_boost_pct=_sample_skill_boost_pct(rng, cfg),
        status="market",
        company_id=None,
        accepted_at=None,
        deadline=None,
        completed_at=None,
        success=None,
        halfway_event_emitted=False,
        requirements=requirements,
    )


def generate_tasks(*, run_seed, count, cfg=None):
    if cfg is None:
        cfg = WorldConfig()
    if count <= 0:
        return []

    streams = RngStreams(run_seed)
    out = []
    for idx in range(1, count + 1):
        rng = streams.stream(f"task_{idx}")
        requirements = _sample_requirements(rng, cfg)
        prestige = _sample_required_prestige(rng, cfg, index=idx - 1)
        out.append(_make_task(rng, cfg, prestige, serial=idx, requirements=requirements))
    return out


def build_task_rows(*, run_seed, count, cfg=None):
    generated = generate_tasks(run_seed=run_seed, count=count, cfg=cfg)
    task_rows = []
    requirement_rows = []

    for task in generated:
        task_rows.append({
            "title": task.title,
            "description": task.description,
            "required_prestige": task.required_prestige,
            "reward_funds_cents": task.reward_funds_cents,
            "reward_prestige_delta": task.reward_prestige_delta,
            "skill_boost_pct": task.skill_boost_pct,
            "status": task.status,
            "company_id": task.company_id,
            "accepted_at": task.accepted_at,
            "deadline": task.deadline,
            "completed_at": task.completed_at,
            "success": task.success,
            "halfway_event_emitted": task.halfway_event_emitted,
        })
        for domain, qty in task.requirements.items():
            requirement_rows.append({
                "_task_title": task.title,
                "domain": domain,
                "required_qty": qty,
                "completed_qty": 0,
            })
    return task_rows, requirement_rows


def generate_replacement_task(*, run_seed, replenish_counter, cfg=None):
    if cfg is None:
        cfg = WorldConfig()
    streams = RngStreams(run_seed)
    rng = streams.stream(f"replenish_{replenish_counter}")
    requirements = _sample_requirements(rng, cfg)
    prestige = _sample_required_prestige(rng, cfg)
    return _make_task(rng, cfg, prestige, serial=replenish_counter, requirements=requirements)


__all__ = [
    "build_task_rows",
    "generate_replacement_task",
    "generate_tasks",
    "GeneratedTask",
]
