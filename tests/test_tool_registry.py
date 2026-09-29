import pytest
from pydantic import ValidationError

from runtime.schemas import ToolCall
from runtime.runner import AgentRuntime
from runtime.tool_registry import ToolRegistry
from tools.service_status import GetServiceStatusTool


def build_runtime() -> AgentRuntime:
    registry = ToolRegistry()
    registry.register(GetServiceStatusTool())

    return AgentRuntime(registry)


def test_execute_valid_tool_call():
    runtime = build_runtime()

    trace = runtime.start_run(
        "Check the payments API."
    )

    result = runtime.execute_tool_call(
        trace,
        ToolCall(
            tool_name="get_service_status",
            arguments={
                "service": "payments-api",
            },
        ),
    )

    assert result["status"] == "degraded"
    assert result["error_rate"] == 0.127

    assert len(trace.steps) == 1

    step = trace.steps[0]

    assert step.tool_name == "get_service_status"
    assert step.tool_arguments == {
        "service": "payments-api"
    }

    assert step.latency_ms is not None


def test_invalid_tool_arguments():
    runtime = build_runtime()

    trace = runtime.start_run(
        "Check service status."
    )

    with pytest.raises(ValidationError):
        runtime.execute_tool_call(
            trace,
            ToolCall(
                tool_name="get_service_status",
                arguments={},
            ),
        )

    assert len(trace.steps) == 1

    step = trace.steps[0]

    assert step.error_type == "ValidationError"


def test_unknown_tool():
    runtime = build_runtime()

    trace = runtime.start_run(
        "Do something invalid."
    )

    with pytest.raises(KeyError):
        runtime.execute_tool_call(
            trace,
            ToolCall(
                tool_name="nonexistent_tool",
                arguments={},
            ),
        )

    assert trace.steps[0].error_type == "KeyError"