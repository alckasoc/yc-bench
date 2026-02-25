from __future__ import annotations

from dataclasses import dataclass

from ..config.schema import WorldConfig
from ..db.models.company import Domain
from .rng import RngStreams, sample_right_skew_triangular_int

_ALL_DOMAINS = list(Domain)


@dataclass(frozen=True)
class GeneratedEmployee:
    name: str
    work_hours_per_day: float
    salary_cents: int
    tier: str
    rates_by_domain: dict[str, float]


def _salary_tiers(cfg):
    return (cfg.salary_junior, cfg.salary_mid, cfg.salary_senior)


def _pick_tier_name(rng, cfg):
    x = rng.random()
    acc = 0.0
    for tier in _salary_tiers(cfg):
        acc += tier.share
        if acc >= x:
            return tier.name
    return _salary_tiers(cfg)[-1].name


def _tier_by_name(cfg, tier_name):
    for tier in _salary_tiers(cfg):
        if tier.name == tier_name:
            return tier
    raise ValueError(f"Tier {tier_name} not found")


def _sample_salary_cents(rng, cfg, tier_name):
    tier = _tier_by_name(cfg, tier_name)
    return sample_right_skew_triangular_int(rng, tier.min_cents, tier.max_cents)


def _sample_rates_by_domain(rng, cfg, tier_name):
    tier = _tier_by_name(cfg, tier_name)
    lo, hi = tier.rate_min, tier.rate_max
    return {domain: round(rng.uniform(lo, hi), 4) for domain in _ALL_DOMAINS}


def generate_employees(*, run_seed, count, cfg=None):
    if cfg is None:
        cfg = WorldConfig()
    if count <= 0:
        return []

    employees = []
    streams = RngStreams(run_seed)

    for idx in range(1, count + 1):
        rng = streams.stream(f"employee_{idx}")
        tier_name = _pick_tier_name(rng, cfg)

        employees.append(
            GeneratedEmployee(
                name=f"Emp_{idx}",
                work_hours_per_day=cfg.work_hours_per_day,
                salary_cents=_sample_salary_cents(rng, cfg, tier_name),
                tier=tier_name,
                rates_by_domain=_sample_rates_by_domain(rng, cfg, tier_name),
            )
        )
    return employees


def build_employee_rows(*, run_seed, company_id, count, cfg=None):
    generated = generate_employees(run_seed=run_seed, count=count, cfg=cfg)
    employee_rows = []
    skill_rows = []

    for emp in generated:
        employee_rows.append(
            {
                "company_id": company_id,
                "name": emp.name,
                "work_hours_per_day": emp.work_hours_per_day,
                "salary_cents": emp.salary_cents,
            }
        )
        for domain, rate in emp.rates_by_domain.items():
            skill_rows.append(
                {
                    "_employee_name": emp.name,
                    "domain": domain,
                    "rate_domain_per_hour": rate,
                }
            )
    return employee_rows, skill_rows


__all__ = [
    "build_employee_rows",
    "GeneratedEmployee",
    "generate_employees",
]
