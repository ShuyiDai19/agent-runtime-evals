from evals.evaluator import evaluate_trace
from evals.schemas import EvalCase
from runtime.runner import AgentRuntime
from runtime.schemas import (
    FinalDecision,
    ToolCall,
    ToolCallDecision,
)
from runtime.tool_registry import ToolRegistry
from tests.fakes import ScriptedModel
from tools.deployments import (
    GetRecentDeploymentsTool,
)
from tools.log_search import SearchLogsTool
from tools.service_status import (
    GetServiceStatusTool,
)


def build_registry() -> ToolRegistry:
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

    return registry


def test_evaluator_passes_good_trajectory():
    model = ScriptedModel(
        decisions=[
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name=(
                        "get_service_status"
                    ),
                    arguments={
                        "service":
                        "payments-api",
                    },
                )
            ),
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name=(
                        "get_recent_deployments"
                    ),
                    arguments={
                        "service":
                        "payments-api",
                    },
                )
            ),
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name="search_logs",
                    arguments={
                        "service":
                        "payments-api",
                        "query":
                        "metadata validation",
                    },
                )
            ),
            FinalDecision(
                final_answer=(
                    "The likely cause is "
                    "v2.4.1 rejecting legacy "
                    "payloads missing "
                    "merchant_context."
                )
            ),
        ]
    )

    runtime = AgentRuntime(
        tool_registry=build_registry(),
        model_client=model,
    )

    trace = runtime.run(
        "Investigate payments-api."
    )

    case = EvalCase(
        id="payments_test",
        task="Investigate payments-api.",
        expected_tools=[
            "get_service_status",
            "get_recent_deployments",
            "search_logs",
        ],
        expected_tool_arguments={
            "get_service_status": {
                "service":
                "payments-api",
            },
            "get_recent_deployments": {
                "service":
                "payments-api",
            },
            "search_logs": {
                "service":
                "payments-api",
            },
        },
        required_answer_terms=[
            "v2.4.1",
            "merchant_context",
        ],
    )

    result = evaluate_trace(
        case=case,
        trace=trace,
    )

    assert result.task_success is True
    assert result.trajectory_pass is True

    assert (
        result.required_tool_coverage
        == 1.0
    )

    assert (
        result.argument_accuracy
        == 1.0
    )

    assert (
        result.answer_term_coverage
        == 1.0
    )

    assert (
        result.duplicate_tool_calls
        == 0
    )

def test_evaluator_detects_duplicate_call():
    model = ScriptedModel(
        decisions=[
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name=(
                        "get_service_status"
                    ),
                    arguments={
                        "service":
                        "payments-api",
                    },
                )
            ),
            ToolCallDecision(
                tool_call=ToolCall(
                    tool_name=(
                        "get_service_status"
                    ),
                    arguments={
                        "service":
                        "payments-api",
                    },
                )
            ),
            FinalDecision(
                final_answer=(
                    "payments-api is degraded."
                )
            ),
        ]
    )

    runtime = AgentRuntime(
        tool_registry=build_registry(),
        model_client=model,
    )

    trace = runtime.run(
        "Check payments-api."
    )

    case = EvalCase(
        id="duplicate_test",
        task="Check payments-api.",
        expected_tools=[
            "get_service_status"
        ],
        expected_tool_arguments={
            "get_service_status": {
                "service":
                "payments-api",
            }
        },
        required_answer_terms=[
            "degraded"
        ],
    )

    result = evaluate_trace(
        case=case,
        trace=trace,
    )

    assert result.task_success is True

    assert (
        result.trajectory_pass
        is False
    )

    assert (
        result.duplicate_tool_calls
        == 1
    )

    assert (
        result.extra_tool_calls
        == 1
    )