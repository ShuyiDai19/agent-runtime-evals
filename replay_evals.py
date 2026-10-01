from __future__ import annotations

import json
from pathlib import Path

from evals.evaluator import evaluate_trace
from evals.report import print_eval_report
from evals.schemas import EvalCase
from runtime.schemas import RunTrace


DATASET_PATH = Path(
    "evals/dataset.json"
)

TRACE_DIR = Path(
    "evals/results/baseline_traces"
)


def load_cases() -> list[EvalCase]:
    raw_cases = json.loads(
        DATASET_PATH.read_text()
    )

    return [
        EvalCase.model_validate(case)
        for case in raw_cases
    ]


def main() -> None:
    cases = load_cases()

    results = []

    for case in cases:
        trace_path = (
            TRACE_DIR
            / f"{case.id}.json"
        )

        if not trace_path.exists():
            print(
                f"Missing trace: {case.id}"
            )
            continue

        trace = RunTrace.model_validate_json(
            trace_path.read_text()
        )

        result = evaluate_trace(
            case=case,
            trace=trace,
        )

        results.append(result)

    print_eval_report(results)


if __name__ == "__main__":
    main()