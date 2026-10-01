from __future__ import annotations

from evals.metrics import (
    answer_term_coverage,
    argument_accuracy,
    duplicate_tool_calls,
    exact_tool_sequence_match,
    extra_tool_calls,
    extract_agent_steps,
    extract_tool_calls,
    repeated_tool_name_calls,
    required_tool_coverage,
    tool_call_efficiency,
    tool_precision,
    total_model_latency_ms,
    total_tool_latency_ms,
)
from evals.schemas import EvalCase, EvalResult
from runtime.schemas import RunStatus, RunTrace


def classify_failures(
    *,
    runtime_succeeded: bool,
    coverage: float,
    precision: float,
    arg_accuracy: float,
    answer_coverage: float,
    duplicates: int,
    repeated_calls: int,
    extras: int,
    sequence_match: bool,
    require_exact_sequence: bool,
) -> list[str]:
    reasons: list[str] = []

    if not runtime_succeeded:
        reasons.append("runtime_failure")

    if coverage < 1.0:
        reasons.append("missing_required_tool")

    if precision < 1.0:
        reasons.append("unnecessary_tool")

    if arg_accuracy < 1.0:
        reasons.append("incorrect_tool_arguments")

    if answer_coverage < 1.0:
        reasons.append("missing_answer_evidence")

    if duplicates > 0:
        reasons.append("duplicate_tool_call")

    if repeated_calls > 0:
        reasons.append("repeated_tool_use")

    if extras > 0:
        reasons.append("extra_tool_call")

    if (
        require_exact_sequence
        and not sequence_match
    ):
        reasons.append("incorrect_tool_sequence")

    return reasons


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
        expected_tools=case.required_tools,
    )

    precision = tool_precision(
        actual_tools=actual_tools,
        expected_tools=case.allowed_tools,
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

    sequence_match = exact_tool_sequence_match(
        actual_tools=actual_tools,
        expected_tools=case.required_tools,
    )

    duplicates = duplicate_tool_calls(
        tool_calls
    )

    repeated_calls = repeated_tool_name_calls(
        actual_tools
    )

    extras = extra_tool_calls(
        actual_tools=actual_tools,
        allowed_tools=case.allowed_tools,
    )

    efficiency = tool_call_efficiency(
        actual_tools=actual_tools,
        expected_tools=case.required_tools,
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
        and repeated_calls == 0
        and (
            sequence_match
            or not case.require_exact_tool_sequence
        )
    )

    failure_reasons = classify_failures(
        runtime_succeeded=runtime_succeeded,
        coverage=coverage,
        precision=precision,
        arg_accuracy=arg_accuracy,
        answer_coverage=answer_coverage,
        duplicates=duplicates,
        repeated_calls=repeated_calls,
        extras=extras,
        sequence_match=sequence_match,
        require_exact_sequence=(
            case.require_exact_tool_sequence
        ),
    )

    return EvalResult(
        case_id=case.id,
        runtime_status=trace.status.value,

        expected_tools=case.required_tools,
        actual_tools=actual_tools,

        required_tool_coverage=coverage,
        tool_precision=precision,
        argument_accuracy=arg_accuracy,
        answer_term_coverage=answer_coverage,

        exact_tool_sequence_match=sequence_match,

        duplicate_tool_calls=duplicates,
        repeated_tool_calls=repeated_calls,
        extra_tool_calls=extras,

        agent_steps=extract_agent_steps(trace),
        tool_calls=len(tool_calls),

        tool_call_efficiency=efficiency,

        task_success=task_success,
        trajectory_pass=trajectory_pass,

        total_latency_ms=(
            trace.total_latency_ms or 0.0
        ),
        model_latency_ms=(
            total_model_latency_ms(trace)
        ),
        tool_latency_ms=(
            total_tool_latency_ms(trace)
        ),

        failure_reasons=failure_reasons,
    )