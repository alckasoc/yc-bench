from __future__ import annotations

from abc import ABC, abstractmethod

class AgentRuntime(ABC):
    @abstractmethod
    def run_turn(self, request):
        raise NotImplementedError

    @abstractmethod
    def clear_session(self, session_id):
        raise NotImplementedError

__all__ = ["AgentRuntime"]