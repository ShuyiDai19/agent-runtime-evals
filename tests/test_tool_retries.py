from pydantic import BaseModel

from runtime.config import RunConfig
from runtime.errors import RetryableToolError
from runtime.runner import AgentRuntime
from runtime.schemas import (
    FinalDecision,
    RunStatus,
    StepType,
    ToolCall,
    ToolCallDecision,
)
from runtime.tool_registry import Tool, ToolRegistry
from tests.fakes import ScriptedModel


class FlakyToolArgs(BaseModel):
    value: str


class FlakyTool(Tool):
    name = "flaky_tool"
    description = "A test tool with transient failures."
    args_schema = FlakyToolArgs

    def __init__(
        self,
        failures_before_success: int,
    ) -> None:
        self.failures_before_success = (
            failures_before_success
        )
        self.calls = 0

    def execute(
        self,
        value: str,
    ) -> dict:
        self.calls += 1

        if (
            self.calls
            <= self.failures_before_success
        ):
            raise RetryableToolError(
                "Temporary service failure."
            )

        return {
            "value": value,
            "attempts": self.calls,
        }

class PermanentFailureTool(FlakyTool):
    name = "permanent_failure_tool"

    def execute(
        self,
        value: str,
    ) -> dict:
        self.calls += 1

        raise ValueError(
            "Invalid request."
        )

def test_runtime_recovers_from_transient_tool_failure():
    tool = FlakyTool(
        failures_before_success=1
    )

    registry = ToolRegistry()
    registry.register(tool)

    model = ScriptedModel(
        decisions=[
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name="flaky_tool",
                    arguments={
                        "value": "hello"
                    },
                )
            ),
            FinalDecision(
                final_answer="Recovered successfully."
            ),
        ]
    )

    runtime = AgentRuntime(
        tool_registry=registry,
        model_client=model,
        config=RunConfig(
            max_tool_retries=2,
            retry_backoff_seconds=0.0,
        ),
    )

    trace = runtime.run(
        "Run the flaky tool."
    )

    assert trace.status == RunStatus.SUCCESS
    assert tool.calls == 2

    tool_steps = [
        step
        for step in trace.steps
        if step.tool_name == "flaky_tool"
    ]

    assert len(tool_steps) == 2

    assert tool_steps[0].attempt == 1
    assert tool_steps[0].step_type == StepType.ERROR
    assert (
        tool_steps[0].error_type
        == "RetryableToolError"
    )

    assert tool_steps[1].attempt == 2
    assert (
        tool_steps[1].step_type
        == StepType.TOOL_CALL
    )

    assert tool_steps[1].tool_result == {
        "value": "hello",
        "attempts": 2,
    }

def test_runtime_stops_after_retry_budget():
    tool = FlakyTool(
        failures_before_success=99
    )

    registry = ToolRegistry()
    registry.register(tool)

    model = ScriptedModel(
        decisions=[
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name="flaky_tool",
                    arguments={
                        "value": "hello"
                    },
                )
            ),
            FinalDecision(
                final_answer=(
                    "The tool remained unavailable."
                )
            ),
        ]
    )

    runtime = AgentRuntime(
        tool_registry=registry,
        model_client=model,
        config=RunConfig(
            max_tool_retries=2,
            retry_backoff_seconds=0.0,
        ),
    )

    trace = runtime.run(
        "Run the flaky tool."
    )

    assert tool.calls == 3

    tool_steps = [
        step
        for step in trace.steps
        if step.tool_name == "flaky_tool"
    ]

    assert len(tool_steps) == 3

    assert [
        step.attempt
        for step in tool_steps
    ] == [1, 2, 3]

    assert all(
        step.step_type == StepType.ERROR
        for step in tool_steps
    )

def test_runtime_does_not_retry_permanent_failure():
    tool = PermanentFailureTool(
        failures_before_success=0
    )

    registry = ToolRegistry()
    registry.register(tool)

    model = ScriptedModel(
        decisions=[
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name=(
                        "permanent_failure_tool"
                    ),
                    arguments={
                        "value": "hello"
                    },
                )
            ),
            FinalDecision(
                final_answer=(
                    "The request was invalid."
                )
            ),
        ]
    )

    runtime = AgentRuntime(
        tool_registry=registry,
        model_client=model,
        config=RunConfig(
            max_tool_retries=5,
            retry_backoff_seconds=0.0,
        ),
    )

    runtime.run(
        "Run the permanent failure tool."
    )

    assert tool.calls == 1