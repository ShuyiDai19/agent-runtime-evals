from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from runtime.schemas import (
    RunStatus,
    RunTrace,
    StepType,
    TraceStep,
    ToolCall,
    utc_now,
)
from runtime.tool_registry import ToolRegistry


class AgentRuntime:
    def __init__(
        self,
        tool_registry: ToolRegistry,
    ) -> None:
        self.tool_registry = tool_registry

    def start_run(
        self,
        task: str,
    ) -> RunTrace:
        return RunTrace(
            run_id=str(uuid4()),
            task=task,
        )

    def execute_tool_call(
        self,
        trace: RunTrace,
        tool_call: ToolCall,
    ):
        step_index = len(trace.steps)

        step = TraceStep(
            step_index=step_index,
            step_type=StepType.TOOL_CALL,
            tool_name=tool_call.tool_name,
            tool_arguments=tool_call.arguments,
        )

        start = perf_counter()

        try:
            result = self.tool_registry.execute(
                tool_name=tool_call.tool_name,
                arguments=tool_call.arguments,
            )

            step.tool_result = result
            return result

        except Exception as exc:
            step.step_type = StepType.ERROR
            step.error_type = type(exc).__name__
            step.error_message = str(exc)
            raise

        finally:
            elapsed = perf_counter() - start

            step.latency_ms = elapsed * 1000
            step.completed_at = utc_now()

            trace.steps.append(step)

    def mark_success(
        self,
        trace: RunTrace,
        final_answer: str,
    ) -> None:
        trace.status = RunStatus.SUCCESS
        trace.final_answer = final_answer
        trace.completed_at = utc_now()

        elapsed = (
            trace.completed_at - trace.started_at
        )

        trace.total_latency_ms = (
            elapsed.total_seconds() * 1000
        )