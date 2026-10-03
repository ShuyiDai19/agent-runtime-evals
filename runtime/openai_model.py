from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from runtime.model import ModelClient
from runtime.schemas import (
    AgentDecision,
    FinalDecision,
    ToolCall,
    ToolCallDecision,
)


SYSTEM_INSTRUCTIONS = """
You are an incident-response agent.

Your job is to answer operational questions and investigate
service incidents using the available tools.

Use the minimum sufficient evidence needed for the user's task.

Rules:

1. Never invent operational facts. Use tools whenever the answer
   requires service status, deployment, or log evidence.

2. Match tool use to the user's intent.

   - Current health or status questions:
     use get_service_status only unless the user asks for diagnosis.

   - Deployment or recent-change questions:
     use get_recent_deployments only.

   - Log, runtime-error, or application-evidence questions:
     use search_logs only unless broader diagnosis is requested.

   - Root-cause incident investigations:
     inspect current service health, recent deployments, and logs
     before concluding when those evidence sources are relevant.

   - Questions asking whether an active incident exists:
     check current status and runtime evidence. A deployment lookup
     may be useful, but is not automatically required.

3. Call at most one tool per model response.

4. Do not call a tool again just to reformulate the same query.
   Reuse evidence already present in the execution history.

5. Only repeat a tool when the previous result was insufficient and
   the new call retrieves materially different information.

6. Before making another tool call, ask whether the available evidence
   is already sufficient to answer the user's actual question.

7. Do not continue investigating beyond the scope of the task.

8. For root-cause conclusions, preserve the important concrete
   evidence in the final answer, such as relevant deployment versions,
   error identifiers, and observed failure symptoms.

9. When there is insufficient evidence for a root cause, say so
   rather than inventing one.

10. When enough evidence has been gathered, return a concise final
    answer.
""".strip()


class OpenAIModelClient(ModelClient):
    def __init__(
        self,
        model: str = "gpt-5.6-luna",
        timeout: float = 30.0,
        max_retries: int = 1,
    ) -> None:
        self.client = OpenAI(
            timeout=timeout,
            max_retries=max_retries,
        )

        self.model = model

    def decide(
        self,
        task: str,
        history: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AgentDecision:
        openai_tools = [
            {
                "type": "function",
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
                "strict": True,
            }
            for tool in tools
        ]

        input_text = self._build_input(
            task=task,
            history=history,
        )

        response = self.client.responses.create(
            model=self.model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=input_text,
            tools=openai_tools,
            tool_choice="auto",
        )

        for item in response.output:
            if item.type == "function_call":
                arguments = json.loads(
                    item.arguments
                )

                return ToolCallDecision(
                    tool_call=ToolCall(
                        tool_name=item.name,
                        arguments=arguments,
                    )
                )

        final_text = response.output_text.strip()

        if not final_text:
            raise RuntimeError(
                "Model returned neither a tool call "
                "nor a final answer."
            )

        return FinalDecision(
            final_answer=final_text
        )

    def _build_input(
        self,
        task: str,
        history: list[dict[str, Any]],
    ) -> str:
        if history:
            history_text = json.dumps(
                history,
                indent=2,
                ensure_ascii=False,
            )
        else:
            history_text = "No tools have been called yet."

        return (
            f"Task:\n{task}\n\n"
            f"Execution history:\n{history_text}"
        )