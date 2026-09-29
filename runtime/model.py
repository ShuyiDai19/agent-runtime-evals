from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from runtime.schemas import AgentDecision


class ModelClient(ABC):
    @abstractmethod
    def decide(
        self,
        task: str,
        history: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AgentDecision:
        raise NotImplementedError