from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class MCPToolResult:
    tool_name: str
    status: str
    data: Any = None
    error: Optional[str] = None


class MCPToolAdapter:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        self._tools[name] = func

    def call(self, name: str, **kwargs: Any) -> MCPToolResult:
        if name not in self._tools:
            return MCPToolResult(tool_name=name, status="error", error=f"Tool {name} not found")

        try:
            return MCPToolResult(tool_name=name, status="success", data=self._tools[name](**kwargs))
        except Exception as exc:  # pragma: no cover - defensive path
            return MCPToolResult(tool_name=name, status="error", error=str(exc))
