from __future__ import annotations

from dataclasses import dataclass, field

from ..db.models.company import Domain
from .rng import RngStreams

_CLIENT_NAME_POOL = [
    "Nexus AI",
    "Vertex Labs",
    "Quantum Dynamics",
    "Atlas Computing",
    "Helix Systems",
    "Orion Data",
    "Cipher Corp",
    "Prism Analytics",
    "Nova Research",
    "Zenith Technologies",
    "Apex Robotics",
    "Stratos Cloud",
    "Vanguard ML",
    "Equinox Labs",
    "Cortex Intelligence",
]

_ALL_DOMAINS = list(Domain)


def _tier_from_multiplier(mult: float) -> str:
    """Map reward multiplier to a visible tier label.

    Standard: [0.7, 1.0)
    Premium:  [1.0, 1.7)
    Enterprise: [1.7, 2.5]
    """
    if mult < 1.0:
        return "Standard"
    if mult < 1.7:
        return "Premium"
    return "Enterprise"


@dataclass(frozen=True)
class GeneratedClient:
    name: str
    reward_multiplier: float  # per-client bonus applied on top of trust reward
    tier: str = "Standard"
    specialty_domains: list[str] = field(default_factory=list)


def generate_clients(*, run_seed: int, count: int) -> list[GeneratedClient]:
    """Generate clients with seeded reward multipliers, tiers, and specialty domains.

    Multipliers range from 0.7 to 2.5 (triangular, mode 1.0).
    Each client gets 1-2 specialty domains (60% get 1, 40% get 2).
    """
    if count <= 0:
        return []
    if count > len(_CLIENT_NAME_POOL):
        raise ValueError(f"count ({count}) exceeds available client names ({len(_CLIENT_NAME_POOL)})")

    streams = RngStreams(run_seed)
    rng = streams.stream("clients")
    names = rng.sample(_CLIENT_NAME_POOL, count)
    clients = []
    for name in names:
        mult = round(rng.triangular(0.7, 2.5, 1.0), 2)
        tier = _tier_from_multiplier(mult)
        # 60% chance of 1 specialty, 40% chance of 2
        n_specialties = 1 if rng.random() < 0.6 else 2
        specialties = [d.value for d in rng.sample(_ALL_DOMAINS, n_specialties)]
        clients.append(GeneratedClient(
            name=name,
            reward_multiplier=mult,
            tier=tier,
            specialty_domains=specialties,
        ))
    return clients


__all__ = ["GeneratedClient", "generate_clients"]
