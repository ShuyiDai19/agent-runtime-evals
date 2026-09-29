from __future__ import annotations

from typing import Any

from runtime.model import ModelClient
from runtime.schemas import AgentDecision


class ScriptedModel(ModelClient):
    def __init__(
        self,
        decisions: list[AgentDecision],
    ) -> None:
        self.decisions = decisions
        self.index = 0

    def decide(
        self,
        task: str,
        history: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AgentDecision:
        if self.index >= len(self.decisions):
            raise RuntimeError(
                "ScriptedModel has no decisions left."
            )

        decision = self.decisions[self.index]

        self.index += 1

        return decision