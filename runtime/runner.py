from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import uuid4

from runtime.config import RunConfig
from runtime.model import ModelClient
from runtime.schemas import (
    FinalDecision,
    RunStatus,
    RunTrace,
    StepType,
    ToolCall,
    ToolCallDecision,
    TraceStep,
    utc_now,
)
from runtime.tool_registry import ToolRegistry


class AgentRuntime:
    def __init__(
        self,
        tool_registry: ToolRegistry,
        model_client: ModelClient,
        config: RunConfig | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.model_client = model_client
        self.config = config or RunConfig()

    def start_run(
        self,
        task: str,
    ) -> RunTrace:
        return RunTrace(
            run_id=str(uuid4()),
            task=task,
        )

    def run(
        self,
        task: str,
    ) -> RunTrace:
        trace = self.start_run(task)

        history: list[dict[str, Any]] = []

        for _ in range(self.config.max_steps):
            try:
                decision = self._get_model_decision(
                    task=task,
                    history=history,
                    trace=trace,
                )
            except Exception as exc:
                self._mark_failed(
                    trace,
                    error_message=str(exc),
                )
                return trace

            if isinstance(decision, FinalDecision):
                self._mark_success(
                    trace,
                    final_answer=decision.final_answer,
                )

                return trace

            if isinstance(decision, ToolCallDecision):
                try:
                    result = self.execute_tool_call(
                        trace=trace,
                        tool_call=decision.tool_call,
                    )
                except Exception as exc:
                    history.append(
                        {
                            "type": "tool_error",
                            "tool_name": decision.tool_call.tool_name,
                            "arguments": decision.tool_call.arguments,
                            "error": str(exc),
                        }
                    )

                    continue

                history.append(
                    {
                        "type": "tool_result",
                        "tool_name": decision.tool_call.tool_name,
                        "arguments": decision.tool_call.arguments,
                        "result": result,
                    }
                )

                continue

            self._mark_failed(
                trace,
                error_message="Unsupported model decision.",
            )

            return trace

        self._mark_max_steps_exceeded(trace)

        return trace

    def _get_model_decision(
        self,
        task: str,
        history: list[dict[str, Any]],
        trace: RunTrace,
    ):
        step = TraceStep(
            step_index=len(trace.steps),
            step_type=StepType.MODEL,
        )

        start = perf_counter()

        try:
            decision = self.model_client.decide(
                task=task,
                history=history,
                tools=self.tool_registry.get_tool_specs(),
            )

            step.model_output = decision.model_dump()

            return decision

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

    def execute_tool_call(
        self,
        trace: RunTrace,
        tool_call: ToolCall,
    ) -> Any:
        step = TraceStep(
            step_index=len(trace.steps),
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

    def _mark_success(
        self,
        trace: RunTrace,
        final_answer: str,
    ) -> None:
        now = utc_now()

        final_step = TraceStep(
            step_index=len(trace.steps),
            step_type=StepType.FINAL,
            message=final_answer,
            started_at=now,
            completed_at=now,
        )

        trace.steps.append(final_step)

        trace.status = RunStatus.SUCCESS
        trace.final_answer = final_answer
        trace.completed_at = now

        self._set_total_latency(trace)

    def _mark_failed(
        self,
        trace: RunTrace,
        error_message: str,
    ) -> None:
        trace.status = RunStatus.FAILED
        trace.error_message = error_message
        trace.completed_at = utc_now()

        self._set_total_latency(trace)

    def _mark_max_steps_exceeded(
        self,
        trace: RunTrace,
    ) -> None:
        trace.status = RunStatus.MAX_STEPS_EXCEEDED
        trace.error_message = (
            f"Agent exceeded maximum of "
            f"{self.config.max_steps} steps."
        )
        trace.completed_at = utc_now()

        self._set_total_latency(trace)

    def _set_total_latency(
        self,
        trace: RunTrace,
    ) -> None:
        if trace.completed_at is None:
            return

        elapsed = (
            trace.completed_at
            - trace.started_at
        )

        trace.total_latency_ms = (
            elapsed.total_seconds() * 1000
        )