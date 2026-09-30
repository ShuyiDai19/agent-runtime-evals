import pytest
from pydantic import ValidationError

from runtime.schemas import ToolCall
from runtime.runner import AgentRuntime
from runtime.tool_registry import ToolRegistry
from tools.service_status import GetServiceStatusTool
from tests.fakes import ScriptedModel
from tools.deployments import GetRecentDeploymentsTool
from tools.log_search import SearchLogsTool


def build_runtime() -> AgentRuntime:
    registry = ToolRegistry()
    registry.register(GetServiceStatusTool())

    unused_model = ScriptedModel(
        decisions=[]
    )

    return AgentRuntime(
        tool_registry=registry,
        model_client=unused_model,
    )


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

def test_registry_exposes_all_incident_tools():
    registry = ToolRegistry()

    registry.register(
        GetServiceStatusTool()
    )

    registry.register(
        GetRecentDeploymentsTool()
    )

    registry.register(
        SearchLogsTool()
    )

    names = {
        tool.name
        for tool in registry.list_tools()
    }

    assert names == {
        "get_service_status",
        "get_recent_deployments",
        "search_logs",
    }