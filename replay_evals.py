from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.evaluator import evaluate_trace
from evals.report import print_eval_report
from evals.schemas import EvalCase
from runtime.schemas import RunTrace


DATASET_PATH = Path("evals/dataset.json")


def load_cases() -> list[EvalCase]:
    raw_cases = json.loads(
        DATASET_PATH.read_text()
    )

    return [
        EvalCase.model_validate(case)
        for case in raw_cases
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--trace-dir",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    cases = load_cases()

    results = []

    for case in cases:
        trace_path = (
            args.trace_dir
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

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            [
                result.model_dump()
                for result in results
            ],
            indent=2,
        )
    )

    print_eval_report(results)


if __name__ == "__main__":
    main()