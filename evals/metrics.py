from __future__ import annotations

import json
from collections import Counter
from typing import Any

from runtime.schemas import RunTrace, StepType


def extract_tool_calls(
    trace: RunTrace,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    for step in trace.steps:
        if step.tool_name is None:
            continue

        calls.append(
            {
                "name": step.tool_name,
                "arguments": (
                    step.tool_arguments or {}
                ),
            }
        )

    return calls


def extract_agent_steps(
    trace: RunTrace,
) -> int:
    return sum(
        1
        for step in trace.steps
        if step.step_type == StepType.MODEL
    )


def required_tool_coverage(
    actual_tools: list[str],
    expected_tools: list[str],
) -> float:
    if not expected_tools:
        return 1.0

    actual_set = set(actual_tools)

    matched = sum(
        1
        for tool in expected_tools
        if tool in actual_set
    )

    return matched / len(expected_tools)


def tool_precision(
    actual_tools: list[str],
    expected_tools: list[str],
) -> float:
    if not actual_tools:
        return 1.0 if not expected_tools else 0.0

    expected_set = set(expected_tools)

    correct = sum(
        1
        for tool in actual_tools
        if tool in expected_set
    )

    return correct / len(actual_tools)


def arguments_match(
    actual_arguments: dict[str, Any],
    expected_arguments: dict[str, Any],
) -> bool:
    return all(
        actual_arguments.get(key) == value
        for key, value in expected_arguments.items()
    )


def argument_accuracy(
    tool_calls: list[dict[str, Any]],
    expected_tool_arguments: dict[
        str,
        dict[str, Any],
    ],
) -> float:
    if not expected_tool_arguments:
        return 1.0

    correct = 0

    for tool_name, expected_args in (
        expected_tool_arguments.items()
    ):
        matching_calls = [
            call
            for call in tool_calls
            if call["name"] == tool_name
        ]

        if any(
            arguments_match(
                call["arguments"],
                expected_args,
            )
            for call in matching_calls
        ):
            correct += 1

    return (
        correct
        / len(expected_tool_arguments)
    )


def answer_term_coverage(
    final_answer: str | None,
    required_terms: list[str],
) -> float:
    if not required_terms:
        return 1.0

    if not final_answer:
        return 0.0

    normalized_answer = final_answer.casefold()

    matched = sum(
        1
        for term in required_terms
        if term.casefold() in normalized_answer
    )

    return matched / len(required_terms)


def exact_tool_sequence_match(
    actual_tools: list[str],
    expected_tools: list[str],
) -> bool:
    return actual_tools == expected_tools


def duplicate_tool_calls(
    tool_calls: list[dict[str, Any]],
) -> int:
    signatures = []

    for call in tool_calls:
        signature = (
            call["name"],
            json.dumps(
                call["arguments"],
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

        signatures.append(signature)

    counts = Counter(signatures)

    return sum(
        count - 1
        for count in counts.values()
        if count > 1
    )


def extra_tool_calls(
    actual_tools: list[str],
    expected_tools: list[str],
) -> int:
    return max(
        len(actual_tools) - len(expected_tools),
        0,
    )


def tool_call_efficiency(
    actual_tools: list[str],
    expected_tools: list[str],
    coverage: float,
) -> float:
    if not expected_tools:
        return 1.0 if not actual_tools else 0.0

    if not actual_tools:
        return 0.0

    overhead_factor = min(
        len(expected_tools) / len(actual_tools),
        1.0,
    )

    return coverage * overhead_factor