from __future__ import annotations
from time import perf_counter
import json
from pathlib import Path

from dotenv import load_dotenv

from evals.evaluator import evaluate_trace
from evals.report import print_eval_report
from evals.schemas import EvalCase
from runtime.openai_model import OpenAIModelClient
from runtime.runner import AgentRuntime
from runtime.tool_registry import ToolRegistry
from tools.deployments import (
    GetRecentDeploymentsTool,
)
from tools.log_search import SearchLogsTool
from tools.service_status import (
    GetServiceStatusTool,
)


DATASET_PATH = Path(
    "evals/dataset.json"
)

RESULTS_DIR = Path(
    "evals/results"
)

TRACES_DIR = RESULTS_DIR / "traces"


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


def load_cases() -> list[EvalCase]:
    raw_cases = json.loads(
        DATASET_PATH.read_text()
    )

    return [
        EvalCase.model_validate(case)
        for case in raw_cases
    ]


def main() -> None:
    load_dotenv()

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TRACES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    runtime = AgentRuntime(
        tool_registry=build_registry(),
        model_client=OpenAIModelClient(),
    )

    cases = load_cases()

    results = []

    for case in cases:
        print(
            f"Running: {case.id}",
            flush=True,
        )

        start = perf_counter()

        trace = runtime.run(
            case.task
        )

        elapsed = perf_counter() - start

        print(
            f"Finished: {case.id} "
            f"({elapsed:.2f}s)",
            flush=True,
        )

        result = evaluate_trace(
            case=case,
            trace=trace,
        )

        results.append(result)

        trace_path = (
            TRACES_DIR
            / f"{case.id}.json"
        )

        trace_path.write_text(
            trace.model_dump_json(
                indent=2,
            )
        )

    results_path = (
        RESULTS_DIR
        / "latest.json"
    )

    results_path.write_text(
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