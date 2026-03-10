# Client Trust System

**Location**: `src/yc_bench/db/models/client.py`, `src/yc_bench/services/generate_clients.py`, `src/yc_bench/core/handlers/task_complete.py`, `src/yc_bench/cli/client_commands.py`

## Overview

Client trust is YC-Bench's second progression axis alongside prestige. While prestige gates *which tasks you can access*, trust determines *how profitable those tasks are*. Every task is offered by a specific client (e.g. "Nexus AI", "Vertex Labs"). Building trust with a client increases payouts and reduces work required, creating a compounding loop that rewards focused relationship-building over scattered effort.

## Design Goals

The trust system was designed to create **genuine strategic diversity** where multiple strategies are viable and no single approach clearly dominates:

| Strategy | Description | Risk | Ceiling |
|----------|-------------|------|---------|
| Domain-aligned focus | Pick clients whose specialties match prestige strengths | Low | Medium-High |
| High-tier gamble | Enterprise clients despite domain mismatch | High | Highest |
| Conservative | Standard-tier, right domains, profitable day 1 | Lowest | Medium |
| Diversified | 3-4 clients, broad coverage | Medium | Medium |
| Trust investor | Cheap tasks from high-tier to build trust early | Medium | High |

## Clients

### Generation (`generate_clients.py`)

Clients are generated at world-seeding time with seeded RNG:

- **Count**: 8 clients (configurable via `num_clients`)
- **Names**: Drawn from a pool of 15 AI company names (e.g. "Nexus AI", "Cipher Corp")
- **Reward multiplier**: `triangular(0.7, 2.5, mode=1.0)` — hidden from the agent
- **Tier**: Derived from multiplier (visible to the agent)
- **Specialty domains**: 1-2 domains per client (60% get 1, 40% get 2)

### Tiers

Tiers are the agent-visible proxy for the hidden reward multiplier:

| Tier | Multiplier Range | Meaning |
|------|-----------------|---------|
| Standard | [0.7, 1.0) | Lower reward ceiling but safer early |
| Premium | [1.0, 1.7) | Moderate scaling |
| Enterprise | [1.7, 2.5] | Highest ceiling but requires high trust to be profitable |

**Design choice**: The exact multiplier is hidden. The agent sees only the tier label via `yc-bench client list`. This prevents the trivial strategy of "always pick the highest multiplier" and requires experimentation to discover which clients are most valuable.

### Specialty Domains

Each client has 1-2 specialty domains (e.g. "research", "training"). Tasks from a client are biased toward their specialties:

- **70% chance** the first domain requirement is a specialty domain
- **30% chance** it's random

This creates domain alignment as a strategic lever — a Premium client whose specialties match your prestige strengths may outperform an Enterprise client in domains where you're weak.

## Trust Mechanics

### Trust Level

Trust is tracked per (company, client) pair in the `ClientTrust` table. Range: [0.0, 5.0].

### Trust Gain (on task success)

```
gain = trust_gain_base × (1 - trust/trust_max)^trust_gain_diminishing_power
```

Default parameters:
- `trust_gain_base`: 0.40
- `trust_gain_diminishing_power`: 1.5
- `trust_max`: 5.0

Diminishing returns mean early trust builds fast (~0.40 per task at trust 0) but slows significantly as trust approaches max (~0.07 per task at trust 4).

### Trust Loss

| Event | Penalty |
|-------|---------|
| Task failure (late) | -0.3 trust |
| Task cancellation | -0.5 trust |

### Trust Decay

Trust decays daily at `trust_decay_per_day` (default: 0.015/day). Inactive client relationships erode over time, requiring continued work to maintain.

### Cross-Client Decay

Completing a task for Client A reduces trust with *all other clients* by `trust_cross_client_decay` (default: 0.03). This models exclusivity pressure — clients notice when you spread attention thin. It penalizes scattered work and rewards focusing on 2-3 key clients.

## Reward Scaling

### Trust Reward Formula

```
actual_reward = listed_reward × trust_multiplier

trust_multiplier = trust_base_multiplier + client_mult² × trust_reward_scale × trust² / trust_max
```

Default parameters:
- `trust_base_multiplier`: 0.50 (everyone starts at 50% of listed reward)
- `trust_reward_scale`: 0.25
- `trust_max`: 5.0

At trust 0, all clients pay 50% of listed reward regardless of tier. At max trust:

| Tier | Example Mult | Trust Multiplier at trust=5 |
|------|-------------|---------------------------|
| Standard | 0.85 | 0.50 + 0.72 × 0.25 × 5 = 1.40 |
| Premium | 1.3 | 0.50 + 1.69 × 0.25 × 5 = 2.61 |
| Enterprise | 2.0 | 0.50 + 4.0 × 0.25 × 5 = 5.50 |

**Design choice**: The quadratic scaling on both multiplier and trust creates dramatic tier separation at high trust while keeping all clients roughly equivalent at low trust. Enterprise clients are actually *worse* than Standard at trust 0 (same 50% payout, but harder tasks due to specialty mismatch), making them a genuine investment gamble.

### Work Reduction

```
work_reduction = trust_work_reduction_max × trust / trust_max
```

Default `trust_work_reduction_max`: 0.40 (up to 40% less work at max trust).

Applied at task acceptance: each domain's `required_qty` is multiplied by `(1 - work_reduction)`. This compounds with higher rewards — at high trust you earn more in less time.

**Design choice**: Work reduction represents "trusted clients give clearer specs." This creates the compounding loop: trust → less work → faster completion → more tasks per month → more trust → even better returns.

## Trust Gating

~20% of tasks have a `required_trust` field (sampled from `triangular(1, 5, mode=2)`). The agent cannot accept these tasks unless trust with the task's client meets the threshold.

```python
if task.required_trust > 0:
    if client_trust < task.required_trust:
        reject("Insufficient trust with client")
```

**Design choice**: Trust-gated tasks are the highest-value opportunities. They ensure that building trust is not just about better payouts but also about unlocking premium work that's invisible to low-trust agents.

## Sim Resume Blocking

To prevent catastrophic payroll drain when the agent has no active work, `sim resume` is **blocked** when there are zero active tasks:

```python
# In sim_commands.py
if active_count == 0:
    return {"ok": False, "error": "BLOCKED: No active tasks..."}
```

The agent loop filters blocked responses (those with `ok: False`) and treats them as no-ops rather than time advances. The auto-advance mechanism in the loop also checks for active tasks before forcing time forward.

**Design choice**: Without this guard, an LLM agent calling `sim resume` while idle would skip months of payroll with zero revenue — a catastrophic and unrecoverable error. The block forces the agent to accept/dispatch work before time can advance.

## Agent Visibility

The agent sees the following via `yc-bench client list`:

```json
{
  "client_id": "uuid",
  "name": "Nexus AI",
  "trust_level": 1.234,
  "tier": "Enterprise",
  "specialties": ["research", "training"]
}
```

**Not visible**: exact reward multiplier, trust formula parameters, cross-client decay rate.

Tasks in `market browse` show `client_name` and `required_trust`. The agent must infer client value by observing actual payouts over time.

## Configuration

All trust parameters are in `WorldConfig` (see `config/schema.py`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_clients` | 8 | Number of clients |
| `trust_max` | 5.0 | Maximum trust level |
| `trust_min` | 0.0 | Minimum trust level |
| `trust_gain_base` | 0.40 | Base trust gain per success |
| `trust_gain_diminishing_power` | 1.5 | Diminishing returns exponent |
| `trust_fail_penalty` | 0.3 | Trust lost on task failure |
| `trust_cancel_penalty` | 0.5 | Trust lost on task cancellation |
| `trust_decay_per_day` | 0.015 | Daily trust decay |
| `trust_cross_client_decay` | 0.03 | Trust erosion with other clients per task |
| `trust_base_multiplier` | 0.50 | Starting reward fraction (all clients) |
| `trust_reward_scale` | 0.25 | Trust reward scaling factor |
| `trust_work_reduction_max` | 0.40 | Max work reduction at max trust |

## Strategic Implications

1. **Focus vs. Diversify**: Cross-client decay penalizes spreading thin, but relying on one client is risky if their specialty doesn't match your prestige growth
2. **Tier vs. Domain**: An Enterprise client in the wrong domain may underperform a Premium client in the right domain
3. **Early vs. Late**: Standard clients are more profitable early (same 50% payout, less specialty mismatch), while Enterprise clients only shine at high trust
4. **Trust as Investment**: Early tasks for a high-tier client are effectively loss-leaders — you earn below-market rates to build a relationship that compounds later
5. **Hidden Information**: The agent must experiment and observe payouts to discover which clients are truly valuable, creating an exploration-exploitation tradeoff
