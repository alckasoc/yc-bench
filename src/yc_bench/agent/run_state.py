"""Run state: tracks the progress and terminal status of a benchmark run."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class TerminalReason(str, Enum):
    BANKRUPTCY = "bankruptcy"
    HORIZON_END = "horizon_end"
    ERROR = "error"


@dataclass
class TranscriptEntry:
    turn: int
    timestamp: str
    user_input: str
    agent_output: str
    commands_executed: List[str] = field(default_factory=list)


@dataclass
class RunState:
    """Mutable state for a single benchmark run."""

    session_id: str
    seed: int
    model: str
    horizon_years: int

    turn_count: int = 0
    terminal: bool = False
    terminal_reason: Optional[TerminalReason] = None
    terminal_detail: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    transcript: List[TranscriptEntry] = field(default_factory=list)
    next_user_input: Optional[str] = None
    total_cost_usd: float = 0.0

    def start(self) -> None:
        self.started_at = datetime.now(timezone.utc).isoformat()

    def record_turn(self, user_input: str, agent_output: str, commands_executed: List[str] | None = None, turn_cost_usd: float = 0.0) -> None:
        self.turn_count += 1
        self.total_cost_usd += turn_cost_usd
        self.transcript.append(TranscriptEntry(
            turn=self.turn_count,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_input=user_input,
            agent_output=agent_output,
            commands_executed=commands_executed or [],
        ))

    def mark_terminal(self, reason: TerminalReason, detail: str = "") -> None:
        self.terminal = True
        self.terminal_reason = reason
        self.terminal_detail = detail
        self.ended_at = datetime.now(timezone.utc).isoformat()

    def should_stop(self) -> bool:
        if self.terminal:
            return True
        return False

    def full_rollout(self) -> Dict[str, Any]:
        """Full results including transcript for saving to disk."""
        return {
            "session_id": self.session_id,
            "model": self.model,
            "seed": self.seed,
            "horizon_years": self.horizon_years,
            "turns_completed": self.turn_count,
            "terminal": self.terminal,
            "terminal_reason": self.terminal_reason.value if self.terminal_reason else None,
            "terminal_detail": self.terminal_detail,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "transcript": [
                {
                    "turn": t.turn,
                    "timestamp": t.timestamp,
                    "user_input": t.user_input,
                    "agent_output": t.agent_output,
                    "commands_executed": t.commands_executed,
                }
                for t in self.transcript
            ],
        }

    def summary(self) -> Dict[str, Any]:
        """Summary without transcript for logging."""
        rollout = self.full_rollout()
        rollout.pop("transcript", None)
        return rollout


__all__ = ["TerminalReason", "TranscriptEntry", "RunState"]
