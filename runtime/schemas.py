from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StepType(str, Enum):
    MODEL = "model"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL = "final"
    ERROR = "error"


class RunStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    MAX_STEPS_EXCEEDED = "max_steps_exceeded"


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

class ToolCallDecision(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    tool_call: ToolCall


class FinalDecision(BaseModel):
    type: Literal["final"] = "final"
    final_answer: str


AgentDecision = ToolCallDecision | FinalDecision

class TraceStep(BaseModel):
    step_index: int
    step_type: StepType

    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    latency_ms: float | None = None

    model_output: dict[str, Any] | None = None

    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None
    tool_result: Any | None = None

    message: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    attempt: int | None = None


class RunTrace(BaseModel):
    run_id: str
    task: str
    status: RunStatus = RunStatus.RUNNING

    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    total_latency_ms: float | None = None

    steps: list[TraceStep] = Field(default_factory=list)

    final_answer: str | None = None
    error_message: str | None = None