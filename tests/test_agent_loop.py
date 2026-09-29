from runtime.config import RunConfig
from runtime.runner import AgentRuntime
from runtime.schemas import (
    FinalDecision,
    RunStatus,
    StepType,
    ToolCall,
    ToolCallDecision,
)
from runtime.tool_registry import ToolRegistry
from tests.fakes import ScriptedModel
from tools.service_status import GetServiceStatusTool


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        GetServiceStatusTool()
    )

    return registry


def test_agent_executes_tool_then_finishes():
    model = ScriptedModel(
        decisions=[
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name="get_service_status",
                    arguments={
                        "service": "payments-api",
                    },
                )
            ),
            FinalDecision(
                final_answer=(
                    "The payments API is degraded."
                )
            ),
        ]
    )

    runtime = AgentRuntime(
        tool_registry=build_registry(),
        model_client=model,
    )

    trace = runtime.run(
        "Check the payments API."
    )

    assert trace.status == RunStatus.SUCCESS

    assert trace.final_answer == (
        "The payments API is degraded."
    )

    assert len(trace.steps) == 4

    assert trace.steps[0].step_type == StepType.MODEL
    assert trace.steps[1].step_type == StepType.TOOL_CALL
    assert trace.steps[2].step_type == StepType.MODEL
    assert trace.steps[3].step_type == StepType.FINAL

    assert (
        trace.steps[1].tool_name
        == "get_service_status"
    )

    assert (
        trace.steps[1].tool_result["status"]
        == "degraded"
    )

def test_agent_stops_after_max_steps():
    model = ScriptedModel(
        decisions=[
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name="get_service_status",
                    arguments={
                        "service": "payments-api",
                    },
                )
            ),
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name="get_service_status",
                    arguments={
                        "service": "payments-api",
                    },
                )
            ),
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name="get_service_status",
                    arguments={
                        "service": "payments-api",
                    },
                )
            ),
        ]
    )

    runtime = AgentRuntime(
        tool_registry=build_registry(),
        model_client=model,
        config=RunConfig(
            max_steps=2,
        ),
    )

    trace = runtime.run(
        "Keep checking forever."
    )

    assert (
        trace.status
        == RunStatus.MAX_STEPS_EXCEEDED
    )

    assert trace.final_answer is None

    assert "maximum of 2 steps" in (
        trace.error_message or ""
    )