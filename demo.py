from runtime.runner import AgentRuntime
from runtime.schemas import ToolCall
from runtime.tool_registry import ToolRegistry
from tools.service_status import GetServiceStatusTool


registry = ToolRegistry()
registry.register(GetServiceStatusTool())

runtime = AgentRuntime(registry)

trace = runtime.start_run(
    "Investigate the payments API."
)

result = runtime.execute_tool_call(
    trace,
    ToolCall(
        tool_name="get_service_status",
        arguments={
            "service": "payments-api",
        },
    ),
)

runtime.mark_success(
    trace,
    final_answer=f"Service result: {result}",
)

print(
    trace.model_dump_json(
        indent=2,
    )
)