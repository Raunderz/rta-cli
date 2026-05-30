import asyncio
import os
from pathlib import Path
from rich.console import Console
from .core.provider import AsyncRtaProvider
from .core.tool_manager import ToolManager
from .core.bash_tool import BashTool
from .core.edit_tool import EditTool
from .core.file_tools import ListDirTool, GrepTool, GlobTool
from .core.session import SessionManager
from .core.context import ContextManager
from .core.loop import Agent
from .core.ui import RtaTUI

async def async_main():
    console = Console()
    console.print("[bold green]Starting Rta CLI v0.5.0 (Async Core)...[/bold green]")

    # 1. Setup Core Components
    provider = AsyncRtaProvider()
    
    tool_manager = ToolManager()
    tool_manager.register_tool(BashTool())
    tool_manager.register_tool(EditTool())
    tool_manager.register_tool(ListDirTool())
    tool_manager.register_tool(GrepTool())
    tool_manager.register_tool(GlobTool())

    # Register MCP Tools
    from rta_cli.mcp import load_mcp_config, list_mcp_tools
    from .core.mcp_tool import MCPToolWrapper
    mcp_config = load_mcp_config()
    for server_name in mcp_config.get("mcpServers", {}):
        mcp_tools = list_mcp_tools(server_name)
        for t_def in mcp_tools:
            tool_manager.register_tool(MCPToolWrapper(server_name, t_def))

    session_path = Path.home() / ".rta" / "history.jsonl"
    session_manager = SessionManager(session_path)
    
    context_manager = ContextManager(provider)
    
    system_prompt = "You are Rta, an expert AI coding assistant. Use tools to help the user."
    
    agent = Agent(
        provider=provider,
        system_prompt=system_prompt,
        tool_manager=tool_manager,
        session_manager=session_manager,
        context_manager=context_manager
    )

    tui = RtaTUI()

    # 2. Main REPL Loop
    while True:
        try:
            user_input = console.input("\n[bold cyan]rta>[/bold cyan] ")
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input.strip():
                continue

            # Run the turn through TUI
            await tui.handle_events(agent.run_turn(user_input))

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user.[/yellow]")
            continue
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
