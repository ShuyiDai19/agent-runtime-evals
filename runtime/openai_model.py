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

Your job is to investigate operational incidents using the
available tools and produce an evidence-based diagnosis.

Rules:
1. Use tools when you need operational evidence.
2. Never invent tool results.
3. Call at most one tool per response.
4. Use previous tool results before deciding the next action.
5. Do not repeat a tool call unless new information makes it necessary.
6. When you have enough evidence, return a concise final diagnosis.
7. Use the minimum sufficient set of tools needed to answer the task.
8. Match tool use to the user's intent:
   - For current service health, use service status only unless diagnosis is requested.
   - For deployment questions, use deployment information only.
   - For runtime or log evidence questions, search logs only unless broader diagnosis is requested.
   - For root-cause incident investigations, gather current health, recent deployments, and logs before concluding.
9. Do not call the same tool multiple times unless the previous result is insufficient or the task explicitly requires multiple searches.
10. Preserve important concrete evidence from tool results in the final answer, including relevant versions, error identifiers, and failure causes.
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