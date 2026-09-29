from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class Tool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel]

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError

    def validate_arguments(
        self,
        arguments: dict[str, Any],
    ) -> BaseModel:
        return self.args_schema.model_validate(arguments)

    def get_spec(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered."
            )

        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown tool: '{name}'."
            ) from exc

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        tool = self.get(tool_name)

        validated = tool.validate_arguments(arguments)

        return tool.execute(**validated.model_dump())

    def get_tool_specs(self) -> list[dict[str, Any]]:
        return [
            tool.get_spec()
            for tool in self._tools.values()
        ]