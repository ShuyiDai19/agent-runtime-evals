from __future__ import annotations

from evals.metrics import (
    answer_term_coverage,
    argument_accuracy,
    duplicate_tool_calls,
    exact_tool_sequence_match,
    extra_tool_calls,
    extract_agent_steps,
    extract_tool_calls,
    required_tool_coverage,
    tool_call_efficiency,
    tool_precision,
)
from evals.schemas import EvalCase, EvalResult
from runtime.schemas import RunStatus, RunTrace


def evaluate_trace(
    case: EvalCase,
    trace: RunTrace,
) -> EvalResult:
    tool_calls = extract_tool_calls(trace)

    actual_tools = [
        call["name"]
        for call in tool_calls
    ]

    coverage = required_tool_coverage(
        actual_tools=actual_tools,
        expected_tools=case.expected_tools,
    )

    precision = tool_precision(
        actual_tools=actual_tools,
        expected_tools=case.expected_tools,
    )

    arg_accuracy = argument_accuracy(
        tool_calls=tool_calls,
        expected_tool_arguments=(
            case.expected_tool_arguments
        ),
    )

    answer_coverage = answer_term_coverage(
        final_answer=trace.final_answer,
        required_terms=case.required_answer_terms,
    )

    sequence_match = (
        exact_tool_sequence_match(
            actual_tools=actual_tools,
            expected_tools=case.expected_tools,
        )
    )

    duplicates = duplicate_tool_calls(
        tool_calls
    )

    extras = extra_tool_calls(
        actual_tools=actual_tools,
        expected_tools=case.expected_tools,
    )

    efficiency = tool_call_efficiency(
        actual_tools=actual_tools,
        expected_tools=case.expected_tools,
        coverage=coverage,
    )

    runtime_succeeded = (
        trace.status == RunStatus.SUCCESS
    )

    task_success = (
        runtime_succeeded
        and coverage == 1.0
        and arg_accuracy == 1.0
        and answer_coverage == 1.0
    )

    trajectory_pass = (
        task_success
        and precision == 1.0
        and duplicates == 0
        and extras == 0
        and (
            sequence_match
            or not case.require_exact_tool_sequence
        )
    )

    return EvalResult(
        case_id=case.id,
        runtime_status=trace.status.value,

        expected_tools=case.expected_tools,
        actual_tools=actual_tools,

        required_tool_coverage=coverage,
        tool_precision=precision,
        argument_accuracy=arg_accuracy,
        answer_term_coverage=answer_coverage,

        exact_tool_sequence_match=(
            sequence_match
        ),

        duplicate_tool_calls=duplicates,
        extra_tool_calls=extras,

        agent_steps=extract_agent_steps(trace),
        tool_calls=len(tool_calls),

        tool_call_efficiency=efficiency,

        task_success=task_success,
        trajectory_pass=trajectory_pass,
    )