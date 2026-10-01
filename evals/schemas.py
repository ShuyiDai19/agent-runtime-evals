from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    id: str
    task: str

    required_tools: list[str] = Field(
        default_factory=list
    )

    allowed_tools: list[str] = Field(
        default_factory=list
    )

    expected_tool_arguments: dict[
        str,
        dict[str, Any],
    ] = Field(default_factory=dict)

    required_answer_terms: list[str] = Field(
        default_factory=list
    )

    require_exact_tool_sequence: bool = False


class EvalResult(BaseModel):
    case_id: str

    runtime_status: str

    expected_tools: list[str]
    actual_tools: list[str]

    required_tool_coverage: float
    tool_precision: float
    argument_accuracy: float
    answer_term_coverage: float

    exact_tool_sequence_match: bool

    duplicate_tool_calls: int
    extra_tool_calls: int

    agent_steps: int
    tool_calls: int

    tool_call_efficiency: float

    task_success: bool
    trajectory_pass: bool

    repeated_tool_calls: int

    total_latency_ms: float
    model_latency_ms: float
    tool_latency_ms: float

    failure_reasons: list[str] = Field(
        default_factory=list
    )

    