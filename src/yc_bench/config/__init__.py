import os

from .loader import load_config
from .schema import ExperimentConfig, AgentConfig, LoopConfig, SimConfig, WorldConfig, SalaryTierConfig


def get_world_config() -> WorldConfig:
    """Load WorldConfig from the active experiment (YC_BENCH_EXPERIMENT env var, default: 'default').

    Falls back to default WorldConfig if config loading fails (e.g. outside a benchmark run).
    """
    try:
        return load_config(os.environ.get("YC_BENCH_EXPERIMENT", "default")).world
    except Exception:
        return WorldConfig()


__all__ = [
    "load_config",
    "get_world_config",
    "ExperimentConfig",
    "AgentConfig",
    "LoopConfig",
    "SimConfig",
    "WorldConfig",
    "SalaryTierConfig",
]
