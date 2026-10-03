from __future__ import annotations

import json
from pathlib import Path
from statistics import mean


BASELINE_PATH = Path(
    "evals/results/baseline_final.json"
)

IMPROVED_PATH = Path(
    "evals/results/improved_final.json"
)


def load_results(path: Path) -> list[dict]:
    return json.loads(
        path.read_text()
    )


def rate(
    results: list[dict],
    field: str,
) -> float:
    return mean(
        float(result[field])
        for result in results
    )


def boolean_rate(
    results: list[dict],
    field: str,
) -> float:
    return mean(
        1.0 if result[field] else 0.0
        for result in results
    )


def summarize(
    results: list[dict],
) -> dict[str, float]:
    return {
        "Task Success": boolean_rate(
            results,
            "task_success",
        ),
        "Trajectory Pass": boolean_rate(
            results,
            "trajectory_pass",
        ),
        "Tool Coverage": rate(
            results,
            "required_tool_coverage",
        ),
        "Tool Precision": rate(
            results,
            "tool_precision",
        ),
        "Argument Accuracy": rate(
            results,
            "argument_accuracy",
        ),
        "Answer Coverage": rate(
            results,
            "answer_term_coverage",
        ),
        "Tool Call Efficiency": rate(
            results,
            "tool_call_efficiency",
        ),
    }


def main() -> None:
    baseline_results = load_results(
        BASELINE_PATH
    )

    improved_results = load_results(
        IMPROVED_PATH
    )

    baseline = summarize(
        baseline_results
    )

    improved = summarize(
        improved_results
    )

    print()
    print("=" * 70)
    print("BASELINE VS IMPROVED")
    print("=" * 70)

    print(
        f"{'Metric':<28}"
        f"{'Baseline':>12}"
        f"{'Improved':>12}"
        f"{'Delta':>12}"
    )

    print("-" * 70)

    for metric in baseline:
        before = baseline[metric]
        after = improved[metric]
        delta = after - before

        print(
            f"{metric:<28}"
            f"{before * 100:>11.1f}%"
            f"{after * 100:>11.1f}%"
            f"{delta * 100:>+11.1f}"
        )

    baseline_extra = sum(
        result["extra_tool_calls"]
        for result in baseline_results
    )

    improved_extra = sum(
        result["extra_tool_calls"]
        for result in improved_results
    )

    print("-" * 70)

    print(
        f"{'Extra Tool Calls':<28}"
        f"{baseline_extra:>12}"
        f"{improved_extra:>12}"
        f"{improved_extra - baseline_extra:>+12}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()