from dotenv import load_dotenv

from runtime.openai_model import OpenAIModelClient
from runtime.runner import AgentRuntime
from runtime.tool_registry import ToolRegistry

load_dotenv()

from tools.deployments import GetRecentDeploymentsTool
from tools.log_search import SearchLogsTool
from tools.service_status import GetServiceStatusTool


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


def main() -> None:
    model = OpenAIModelClient()

    runtime = AgentRuntime(
        tool_registry=build_registry(),
        model_client=model,
    )

    trace = runtime.run(
        (
            "Investigate why payments-api is degraded. "
            "Check its current health, recent deployments, "
            "and logs before giving the most likely cause."
        )
    )

    print(
        trace.model_dump_json(
            indent=2,
        )
    )


if __name__ == "__main__":
    main()