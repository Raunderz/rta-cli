import sys
import asyncio
from typing import Optional, Dict
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.spinner import Spinner
from .events import (
    Event, ThinkingStartEvent, ThinkingDeltaEvent, ThinkingEndEvent,
    TextStartEvent, TextDeltaEvent, TextEndEvent,
    ToolStartEvent, ToolArgsDeltaEvent, ToolEndEvent,
    ToolResultEvent, TurnEndEvent, ErrorEvent
)

class RtaTUI:
    def __init__(self):
        self.console = Console()
        self.live: Optional[Live] = None
        
        # Current state
        self.thinking_content = ""
        self.text_content = ""
        self.active_tools: Dict[str, Dict] = {} # id -> {name, args, result}

    def _render_thinking(self) -> Panel:
        return Panel(
            Text(self.thinking_content, style="italic dim"),
            title="[bold blue]Thinking[/bold blue]",
            border_style="blue"
        )

    def _render_response(self) -> Markdown:
        return Markdown(self.text_content)

    def _render_tool(self, tool_id: str) -> Panel:
        tool = self.active_tools[tool_id]
        status = "[yellow]Executing...[/yellow]"
        if tool.get("result"):
            res = tool["result"]
            status = "[green]Success[/green]" if res.success else "[red]Failed[/red]"
            content = res.ui_details or res.result
        else:
            content = f"Args: {tool['args']}"

        return Panel(
            Text(content),
            title=f"[bold cyan]{tool['name']}[/bold cyan] {status}",
            border_style="cyan"
        )

    def _generate_display(self):
        from rich.console import Group
        elements = []
        
        if self.thinking_content:
            elements.append(self._render_thinking())
        
        if self.text_content:
            elements.append(self._render_response())
            
        for tid in self.active_tools:
            elements.append(self._render_tool(tid))
            
        return Group(*elements)

    async def handle_events(self, event_stream):
        with Live(self._generate_display(), console=self.console, refresh_per_second=10) as live:
            self.live = live
            async for event in event_stream:
                if isinstance(event, ThinkingDeltaEvent):
                    self.thinking_content += event.delta
                elif isinstance(event, ThinkingEndEvent):
                    # We keep thinking content but maybe dim it more or move it
                    pass
                elif isinstance(event, TextDeltaEvent):
                    self.text_content += event.delta
                elif isinstance(event, ToolStartEvent):
                    self.active_tools[event.tool_call_id] = {"name": event.name, "args": ""}
                elif isinstance(event, ToolArgsDeltaEvent):
                    self.active_tools[event.tool_call_id]["args"] += event.delta
                elif isinstance(event, ToolResultEvent):
                    self.active_tools[event.tool_call_id]["result"] = event.result
                elif isinstance(event, ErrorEvent):
                    self.console.print(f"[bold red]Error: {event.message}[/bold red]")
                    if event.details:
                        self.console.print(f"[dim]{event.details}[/dim]")
                
                self.live.update(self._generate_display())

        # Final cleanup/newline
        self.console.print()
