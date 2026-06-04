from __future__ import annotations
import time
import asyncio
import random
from typing import Optional, Dict
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.spinner import Spinner
from rich.rule import Rule
from .events import (
    ThinkingStartEvent,
    ThinkingDeltaEvent,
    ThinkingEndEvent,
    TextDeltaEvent,
    ToolStartEvent,
    ToolArgsDeltaEvent,
    ToolResultEvent,
    TurnEndEvent,
    UsageEvent,
    ErrorEvent,
)

LOADING_MESSAGES = [
    "Navigating the codebase...",
    "Herding electrons...",
    "Consulting the silicon gods...",
    "Decrypting spaghetti code...",
    "Optimizing orbits...",
    "Refactoring the universe...",
    "Avoiding infinite loops...",
    "Polishing pixels...",
    "Chasing segment faults...",
    "Compiling thoughts...",
    "Summoning the logic...",
    "Rewriting the future...",
    "Chasing bugs in the dark...",
    "Parsing complexity...",
    "Thinking in 4 Dimensions...",
    "Reticulating splines...",
    "Consulting the digital oracle...",
    "Synthesizing silicon wisdom...",
    "Tuning the neural arrays...",
    "Gathering silicon wisdom...",
    "Architecting a solution...",
    "Traversing the latent space...",
]


class RtaTUI:
    def __init__(self):
        self.console = Console()
        self.live: Optional[Live] = None
        self.start_time = time.time()

        # Current state
        self.thinking_content = ""
        self.is_thinking = False
        self.text_content = ""
        self.active_tools: Dict[str, Dict] = {}  # id -> {name, args, result}
        self.loading = False
        self.total_in = 0
        self.total_out = 0
        self.char_in = 0
        self.char_out = 0

    def _render_loading(self) -> Panel:
        msg = random.choice(LOADING_MESSAGES)
        return Panel(
            Group(Spinner("dots", style="cyan"), Text(f" {msg}", style="cyan")),
            border_style="dim",
            padding=(1, 2),
        )

    def _render_thinking(self) -> Panel:
        title = "[bold blue]Thinking[/bold blue]"
        if self.is_thinking:
            title = Group(
                Spinner("dots", style="blue"), Text(" Thinking", style="bold blue")
            )

        return Panel(
            Text(self.thinking_content.strip(), style="italic dim"),
            title=title,
            border_style="blue",
            padding=(0, 1),
        )

    def _render_response(self) -> Group:
        return Group(Rule(style="dim"), Markdown(self.text_content), Rule(style="dim"))

    def _render_tool(self, tool_id: str) -> Panel:
        tool = self.active_tools[tool_id]
        status = "[yellow]Executing...[/yellow]"
        if tool.get("result"):
            res = tool["result"]
            status = "[green]Done[/green]" if res.success else "[red]Error[/red]"
            content = res.ui_summary or res.result.split("\n")[0]
            if not res.success:
                content = f"[red]{res.result}[/red]"
        else:
            content = f"Arguments: {tool['args']}"

        return Panel(
            Text(content, overflow="ellipsis"),
            title=f"[bold cyan]Tool: {tool['name']}[/bold cyan] {status}",
            border_style="cyan",
            padding=(0, 1),
        )

    def _generate_display(self):
        if self.loading:
            return self._render_loading()

        elements = []

        if self.thinking_content:
            elements.append(self._render_thinking())

        if self.text_content:
            elements.append(self._render_response())

        for tid in self.active_tools:
            elements.append(self._render_tool(tid))

        return Group(*elements)

    def track_input(self, text: str):
        self.char_in += len(text)

    async def handle_events(self, event_stream):
        # Reset state for new turn
        self.thinking_content = ""
        self.text_content = ""
        self.active_tools = {}
        self.is_thinking = False
        self.loading = True

        try:
            with Live(
                self._generate_display(),
                console=self.console,
                refresh_per_second=10,
                transient=False,
            ) as live:
                self.live = live
                async for event in event_stream:
                    if self.loading and not isinstance(event, ErrorEvent):
                        self.loading = False
                    if isinstance(event, ThinkingStartEvent):
                        self.is_thinking = True
                    elif isinstance(event, ThinkingDeltaEvent):
                        self.thinking_content += event.delta
                    elif isinstance(event, ThinkingEndEvent):
                        self.is_thinking = False
                        self.thinking_content = event.thinking
                    elif isinstance(event, TextDeltaEvent):
                        self.text_content += event.delta
                        self.char_out += len(event.delta)
                    elif isinstance(event, ToolStartEvent):
                        self.active_tools[event.tool_call_id] = {
                            "name": event.name,
                            "args": "",
                        }
                    elif isinstance(event, ToolArgsDeltaEvent):
                        self.active_tools[event.tool_call_id]["args"] += event.delta
                    elif isinstance(event, ToolResultEvent):
                        self.active_tools[event.tool_call_id]["result"] = event.result
                    elif isinstance(event, UsageEvent):
                        if event.prompt_tokens:
                            self.total_in += event.prompt_tokens
                        if event.completion_tokens:
                            self.total_out += event.completion_tokens
                    elif isinstance(event, TurnEndEvent):
                        from rta_cli.notify import notify

                        notify("completion")
                    elif isinstance(event, ErrorEvent):
                        self.loading = False
                        self.console.print(
                            f"\n[bold red]Error: {event.message}[/bold red]"
                        )
                        if event.details:
                            self.console.print(f"[dim]{event.details}[/dim]")
                        from rta_cli.notify import notify

                        notify("error")

                    if self.live:
                        self.live.update(self._generate_display())
        except asyncio.CancelledError:
            self.console.print("\n[yellow]Turn cancelled.[/yellow]")
        except Exception as e:
            self.console.print(f"\n[bold red]TUI Error: {str(e)}[/bold red]")
        finally:
            self.live = None

        self.console.print()

    def print_summary(self):
        duration = time.time() - self.start_time
        mins, secs = divmod(int(duration), 60)
        in_tokens = self.total_in or self.char_in // 4
        out_tokens = self.total_out or self.char_out // 4
        self.console.print(
            f"\n[dim]─ Session: {mins}m {secs}s | In: {in_tokens} | Out: {out_tokens} ─[/]\n"
        )
