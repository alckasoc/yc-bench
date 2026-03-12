"""Pydantic models for all experiment configuration.

Every tunable parameter lives here. TOML files are validated against these
models — Pydantic catches typos and type errors at load time.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .sampling import BetaDist, ConstantDist, NormalDist, TriangularDist, UniformDist, DistSpec  # noqa: F401


# ---------------------------------------------------------------------------
# Salary tier
# ---------------------------------------------------------------------------

class SalaryTierConfig(BaseModel):
    name: str
    share: float          # fraction of employees in this tier (all tiers must sum to 1.0)
    min_cents: int        # minimum monthly salary in cents
    max_cents: int        # maximum monthly salary in cents
    rate_min: float       # minimum skill rate (units/hour)
    rate_max: float       # maximum skill rate (units/hour)


# ---------------------------------------------------------------------------
# World distributions
#
# Each field names a random quantity in world generation and specifies which
# distribution family + parameters to use. Changing `type` switches families;
# changing parameters tunes the shape. See config/sampling.py for all families.
# ---------------------------------------------------------------------------

class WorldDists(BaseModel):
    # Prestige level required to accept a task (result cast to int).
    # Any DistSpec family works — e.g. constant for ablations, uniform for flat sampling.
    required_prestige: DistSpec = Field(
        default_factory=lambda: TriangularDist(low=1, high=10, mode=1)
    )
    # Base reward paid on task completion, in cents (result cast to int).
    reward_funds_cents: DistSpec = Field(
        default_factory=lambda: TriangularDist(low=300_000, high=4_000_000, mode=1_400_000)
    )
    # Number of domains required per task (result cast to int).
    domain_count: DistSpec = Field(
        default_factory=lambda: TriangularDist(low=1, high=3, mode=1)
    )
    # Work units required per domain (result cast to int).
    required_qty: DistSpec = Field(
        default_factory=lambda: TriangularDist(low=200, high=3000, mode=800)
    )
    # Prestige delta awarded per domain on task success.
    # Mean ~0.1: climbing from prestige 1→5 takes ~40 tasks.
    reward_prestige_delta: DistSpec = Field(
        default_factory=lambda: BetaDist(alpha=1.2, beta=2.8, scale=0.35, low=0.0, high=0.35)
    )
    # Trust level required to accept exclusive tasks (sampled for ~20% of tasks).
    required_trust: DistSpec = Field(
        default_factory=lambda: TriangularDist(low=1, high=5, mode=2)
    )
    # Skill rate boost fraction applied to each assigned employee on task success.
    skill_boost: DistSpec = Field(
        default_factory=lambda: NormalDist(mean=0.12, stdev=0.06, low=0.01, high=0.40)
    )


# ---------------------------------------------------------------------------
# Agent / LLM
# ---------------------------------------------------------------------------

class AgentConfig(BaseModel):
    model: str = "openrouter/z-ai/glm-5"
    temperature: float = 0.0
    top_p: float = 1.0
    request_timeout_seconds: float = 300.0
    retry_max_attempts: int = 3
    retry_backoff_seconds: float = 1.0
    # Conversation rounds kept in context before each API call; older rounds dropped.
    history_keep_rounds: int = 20
    # Optional system prompt override. None = use default from agent/prompt.py
    system_prompt: str | None = None


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

class LoopConfig(BaseModel):
    # Consecutive turns without `sim resume` before the loop forces a time-advance.
    auto_advance_after_turns: int = 10
    # Hard cap on total turns. null = unlimited.
    max_turns: int | None = None


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class SimConfig(BaseModel):
    start_date: str = "2025-01-01"    # ISO 8601 (YYYY-MM-DD)
    horizon_years: int = 3
    company_name: str = "BenchCo"


# ---------------------------------------------------------------------------
# World generation
# ---------------------------------------------------------------------------

class WorldConfig(BaseModel):
    # --- Workforce ---
    num_employees: int = 10
    initial_funds_cents: int = 15_000_000    # $150,000
    initial_prestige_level: float = 1.0
    work_hours_per_day: float = 9.0

    # --- Market ---
    num_market_tasks: int = 500
    market_browse_default_limit: int = 50

    # --- Salary bump on task completion ---
    salary_bump_pct: float = 0.01    # 1% raise per assigned employee per completed task
    salary_max_cents: int = 10_000_000  # cap individual salary at $100K/month
    skill_rate_max: float = 30.0  # cap employee skill rate (prevents exponential skill compounding)

    # --- Prestige mechanics ---
    prestige_max: float = 10.0
    prestige_min: float = 1.0
    penalty_fail_multiplier: float = 0.8
    penalty_cancel_multiplier: float = 1.2
    # Extra reward fraction per prestige level above 1.
    # At 0.55: prestige-8 tasks pay ~4.85x more than prestige-1.
    reward_prestige_scale: float = 0.3

    # Daily prestige decay per domain. Domains not exercised lose prestige
    # over time: -0.01/day → -0.3/month → untouched domain drops ~1 level
    # every ~3 months. Floored at prestige_min.
    prestige_decay_per_day: float = 0.005

    # --- Client trust (intuitive knobs) ---
    num_clients: int = 8
    trust_max: float = 5.0
    # ~how many successful tasks to reach 80% of max trust with one client
    trust_build_rate: float = 20.0
    # 0-1: how punishing failures/inactivity are (0=forgiving, 1=harsh)
    trust_fragility: float = 0.5
    # 0-1: how much working for one client hurts trust with others (0=none, 1=heavy)
    trust_focus_pressure: float = 0.5
    # payout multiplier a typical Premium client (mult≈1.3) gives at max trust
    trust_reward_ceiling: float = 2.6
    # max work reduction at max trust (0.4 = 40% less work)
    trust_work_reduction_max: float = 0.40
    # fraction of tasks that require trust (~0.2 = 20%)
    trust_gating_fraction: float = 0.20

    # --- Derived trust params (computed from knobs above, do not set directly) ---
    trust_min: float = 0.0
    trust_gain_base: float = 0.0
    trust_gain_diminishing_power: float = 1.5
    trust_fail_penalty: float = 0.0
    trust_cancel_penalty: float = 0.0
    trust_decay_per_day: float = 0.0
    trust_cross_client_decay: float = 0.0
    trust_base_multiplier: float = 0.50
    trust_reward_scale: float = 0.0
    trust_reward_threshold: float = 0.0
    trust_reward_ramp: float = 0.0
    trust_level_reward_scale: float = 3.0
    trust_level_max_required: int = 4
    trust_gated_reward_boost: float = 0.15
    client_reward_mult_low: float = 0.7
    client_reward_mult_high: float = 2.5
    client_reward_mult_mode: float = 1.0
    client_single_specialty_prob: float = 0.6
    client_tier_premium_threshold: float = 1.0
    client_tier_enterprise_threshold: float = 1.7
    task_specialty_domain_bias: float = 0.7

    # Required qty scaling by prestige: qty *= 1 + prestige_qty_scale * (prestige - 1).
    # At 0.3: prestige-5 tasks need 2.2× the work of prestige-1 tasks.
    prestige_qty_scale: float = 0.3

    # --- Deadline computation ---
    deadline_qty_per_day: float = 150.0  # max per-domain qty / this = deadline days
    deadline_min_biz_days: int = 7

    # --- Progress milestones (fraction thresholds that trigger checkpoint events) ---
    task_progress_milestones: list[float] = Field(default_factory=lambda: [0.25, 0.5, 0.75])

    # --- Business hours ---
    workday_start_hour: int = 9
    workday_end_hour: int = 18

    # --- Distributions (shape of random draws during world generation) ---
    dist: WorldDists = Field(default_factory=WorldDists)

    # --- Salary tiers ---
    salary_junior: SalaryTierConfig = Field(
        default_factory=lambda: SalaryTierConfig(
            name="junior", share=0.50,
            min_cents=200_000, max_cents=400_000,
            rate_min=1.0, rate_max=4.0,
        )
    )
    salary_mid: SalaryTierConfig = Field(
        default_factory=lambda: SalaryTierConfig(
            name="mid", share=0.35,
            min_cents=600_000, max_cents=800_000,
            rate_min=4.0, rate_max=7.0,
        )
    )
    salary_senior: SalaryTierConfig = Field(
        default_factory=lambda: SalaryTierConfig(
            name="senior", share=0.15,
            min_cents=1_000_000, max_cents=1_500_000,
            rate_min=7.0, rate_max=10.0,
        )
    )

    @model_validator(mode="after")
    def _derive_trust_params(self) -> WorldConfig:
        """Derive detailed trust parameters from the intuitive knobs.

        Derivation preserves default behavior: trust_build_rate=20, fragility=0.5,
        focus_pressure=0.5, reward_ceiling=2.6 produce the same values as the
        original hardcoded defaults.
        """
        # trust_build_rate → gain_base
        # Approximate: gain_base ≈ trust_max × 1.6 / build_rate
        # At default (20): 5.0 × 1.6 / 20 = 0.40
        self.trust_gain_base = self.trust_max * 1.6 / self.trust_build_rate

        # trust_fragility → fail_penalty, cancel_penalty, decay_per_day
        # At 0.5: fail=0.3, cancel=0.5, decay=0.015
        self.trust_fail_penalty = self.trust_fragility * 0.6
        self.trust_cancel_penalty = self.trust_fragility * 1.0
        self.trust_decay_per_day = self.trust_fragility * 0.03

        # trust_focus_pressure → cross_client_decay
        # At 0.5: cross_client_decay = 0.03
        self.trust_cross_client_decay = self.trust_focus_pressure * 0.06

        # trust_reward_ceiling → reward_scale
        # ceiling = base_multiplier + ref_mult² × scale × trust_max
        # Using Premium reference (mult≈1.3): scale = (ceiling - 0.50) / (1.69 × trust_max)
        ref_mult_sq = 1.69  # 1.3²
        self.trust_reward_scale = (
            (self.trust_reward_ceiling - self.trust_base_multiplier)
            / (ref_mult_sq * self.trust_max)
        )

        # trust_gating_fraction → threshold + ramp
        # At 0.2: threshold=0.6, ramp=0.4 (top 40% CAN require, effective ~20%)
        self.trust_reward_threshold = max(0.0, 1.0 - 2.0 * self.trust_gating_fraction)
        self.trust_reward_ramp = min(1.0, 2.0 * self.trust_gating_fraction)

        return self

    @model_validator(mode="after")
    def _salary_shares_sum_to_one(self) -> WorldConfig:
        total = self.salary_junior.share + self.salary_mid.share + self.salary_senior.share
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"salary tier shares must sum to 1.0, got {total:.6f}")
        return self


# ---------------------------------------------------------------------------
# Top-level experiment
# ---------------------------------------------------------------------------

class ExperimentConfig(BaseModel):
    name: str = "default"
    description: str = ""
    agent: AgentConfig = Field(default_factory=AgentConfig)
    loop: LoopConfig = Field(default_factory=LoopConfig)
    sim: SimConfig = Field(default_factory=SimConfig)
    world: WorldConfig = Field(default_factory=WorldConfig)


__all__ = [
    "AgentConfig",
    "DistSpec",
    "ExperimentConfig",
    "LoopConfig",
    "SalaryTierConfig",
    "SimConfig",
    "WorldConfig",
    "WorldDists",
]
