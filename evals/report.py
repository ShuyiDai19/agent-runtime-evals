from __future__ import annotations

from statistics import mean

from evals.schemas import EvalResult


def percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def print_eval_report(
    results: list[EvalResult],
) -> None:
    if not results:
        print("No evaluation results.")
        return

    task_success_rate = mean(
        1.0 if result.task_success else 0.0
        for result in results
    )

    trajectory_pass_rate = mean(
        1.0 if result.trajectory_pass else 0.0
        for result in results
    )

    avg_tool_coverage = mean(
        result.required_tool_coverage
        for result in results
    )

    avg_tool_precision = mean(
        result.tool_precision
        for result in results
    )

    avg_argument_accuracy = mean(
        result.argument_accuracy
        for result in results
    )

    avg_answer_coverage = mean(
        result.answer_term_coverage
        for result in results
    )

    avg_efficiency = mean(
        result.tool_call_efficiency
        for result in results
    )

    total_duplicates = sum(
        result.duplicate_tool_calls
        for result in results
    )

    total_extra_calls = sum(
        result.extra_tool_calls
        for result in results
    )

    print()
    print("=" * 52)
    print("AGENT EVALUATION REPORT")
    print("=" * 52)

    for result in results:
        status = (
            "PASS"
            if result.trajectory_pass
            else "FAIL"
        )

        print(
            f"{result.case_id:<30}"
            f"{status:>10}"
        )

        if result.failure_reasons:
            reasons = ", ".join(
                result.failure_reasons
            )

            print(
                f"  -> {reasons}"
            )

    print("-" * 52)

    print(
        f"{'Cases':<30}"
        f"{len(results):>10}"
    )

    print(
        f"{'Task Success':<30}"
        f"{percentage(task_success_rate):>10}"
    )

    print(
        f"{'Trajectory Pass':<30}"
        f"{percentage(trajectory_pass_rate):>10}"
    )

    print(
        f"{'Required Tool Coverage':<30}"
        f"{percentage(avg_tool_coverage):>10}"
    )

    print(
        f"{'Tool Precision':<30}"
        f"{percentage(avg_tool_precision):>10}"
    )

    print(
        f"{'Argument Accuracy':<30}"
        f"{percentage(avg_argument_accuracy):>10}"
    )

    print(
        f"{'Answer Term Coverage':<30}"
        f"{percentage(avg_answer_coverage):>10}"
    )

    print(
        f"{'Tool Call Efficiency':<30}"
        f"{percentage(avg_efficiency):>10}"
    )

    print(
        f"{'Duplicate Tool Calls':<30}"
        f"{total_duplicates:>10}"
    )

    print(
        f"{'Extra Tool Calls':<30}"
        f"{total_extra_calls:>10}"
    )

    print("=" * 52)