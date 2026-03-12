# Client Trust System

**Location**: `services/generate_clients.py`, `services/generate_tasks.py`, `core/handlers/task_complete.py`, `cli/task_commands.py`

## Overview

Trust is the second progression axis alongside prestige. Prestige gates task access; trust determines profitability. Every task belongs to a client. Building trust increases payouts and reduces work, rewarding focused relationship-building.

## Configuration

The trust system is controlled by **7 intuitive knobs** in `WorldConfig`. All internal parameters are derived automatically.

| Knob | Default | Meaning |
|------|---------|---------|
| `num_clients` | 8 | Number of clients in the game |
| `trust_max` | 5.0 | Maximum trust level |
| `trust_build_rate` | 20.0 | ~tasks to reach 80% max trust with one client |
| `trust_fragility` | 0.5 | 0–1: how punishing failures/inactivity are |
| `trust_focus_pressure` | 0.5 | 0–1: penalty for spreading work across clients |
| `trust_reward_ceiling` | 2.6 | Payout multiplier a Premium client gives at max trust |
| `trust_work_reduction_max` | 0.40 | Max work reduction at max trust (40%) |
| `trust_gating_fraction` | 0.20 | Fraction of tasks that require trust (~20%) |

### Derivation

These knobs derive all internal parameters via `_derive_trust_params()`:

```
gain_base           = trust_max × 1.6 / trust_build_rate
fail_penalty        = fragility × 0.6
cancel_penalty      = fragility × 1.0
decay_per_day       = fragility × 0.03
cross_client_decay  = focus_pressure × 0.06
reward_scale        = (reward_ceiling - 0.50) / (1.69 × trust_max)
reward_threshold    = 1.0 - 2 × gating_fraction
reward_ramp         = 2 × gating_fraction
```

## Client Generation

At world-seeding time, `num_clients` clients are generated with:
- **Reward multiplier**: `triangular(0.7, 2.5, mode=1.0)` — hidden from agent
- **Tier** (visible): Standard `[0.7, 1.0)`, Premium `[1.0, 1.7)`, Enterprise `[1.7, 2.5]`
- **Specialties**: 1 domain (60%) or 2 domains (40%)

## Task Domain Bias

First domain pick has 70% chance of matching client specialty. Remaining domains uniform random.

## Trust Gating

High-reward tasks may require trust:

```
reward_frac = (reward - floor) / (ceiling - floor)
trust_prob  = max(0, (reward_frac - threshold) / ramp)
level       = clamp(1 + reward_frac × 3, 1, 4)
```

Trust-gated tasks get a 15% reward boost per required trust level.

**Why**: Clients reserve best projects for proven vendors.

## Trust Reward Formula (at task accept)

```
trust_multiplier = 0.50 + client_mult² × reward_scale × trust² / trust_max
actual_reward    = listed_reward × trust_multiplier
```

At trust 0, everyone gets 50% of listed reward. At max trust:

| Tier | mult | multiplier |
|------|------|-----------|
| Standard | 0.85 | 1.40× |
| Premium | 1.30 | 2.60× |
| Enterprise | 2.00 | 5.50× |

**Why**: Quadratic on both mult and trust creates dramatic tier separation at high trust. Enterprise is worse than Standard at trust 0 — a genuine investment gamble.

## Work Reduction (at task accept)

```
work_reduction = trust_work_reduction_max × trust / trust_max
required_qty  *= (1 - work_reduction)
```

**Why**: Trusted clients give clearer specs. Creates virtuous cycle: trust → less work → faster completion → more tasks → more trust.

## Trust Gain (task success)

```
gain = gain_base × (1 - trust/trust_max) ^ 1.5
```

Diminishing returns: ~0.40/task at trust 0, ~0.07/task at trust 4.

## Trust Loss

| Event | Penalty |
|-------|---------|
| Task failure | `fragility × 0.6` (default 0.3) |
| Task cancel | `fragility × 1.0` (default 0.5) |

## Trust Decay

- **Daily**: `fragility × 0.03` per day (default 0.015)
- **Cross-client**: `focus_pressure × 0.06` per task for other client (default 0.03)

**Why**: Cross-client decay penalizes scattering and rewards focusing on 2–3 clients.

## Sim Resume When Idle

`sim resume` is allowed even with no active tasks — time moves forward regardless. Calling it while idle advances to the next payroll event, burning runway with zero revenue. The prompt warns the agent not to do this, but doesn't prevent it. If the agent ignores the warning and burns payroll, that's a valid failure mode.

## Agent Visibility

Visible: client name, trust_level, tier, specialties. Not visible: exact multiplier, formulas, decay rates.
