import asyncio
import json
import time
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
from .core.events import UsageEvent
from rta_cli.discovery import discover_project

async def async_main():
    console = Console()
    console.print("[bold green]Starting Rta CLI v0.5.0 (Async Core)...[/bold green]")

    # 1. Setup Core Components
    provider = AsyncRtaProvider()
    cwd = os.getcwd()
    project_info = await asyncio.to_thread(discover_project, cwd)
    
    tool_manager = ToolManager()
    tool_manager.register_tool(BashTool())
    tool_manager.register_tool(EditTool())
    tool_manager.register_tool(ListDirTool())
    tool_manager.register_tool(GrepTool())
    tool_manager.register_tool(GlobTool())

    from .core.lsp_tools import GetDiagnosticsTool, GoToDefinitionTool
    tool_manager.register_tool(GetDiagnosticsTool(cwd))
    tool_manager.register_tool(GoToDefinitionTool(cwd))

    from .core.legacy_tools import (
        DiscoverProjectTool, GetFileContentsTool, GetFilesInfoTool,
        WriteFileTool, DeleteFileTool, CreateDirTool, ApplyDiffTool,
        EditFileAstTool, ListSkillsTool, SemanticSearchTool,
        GetRepoSkeletonTool, QuestionTool,
        GitStatusTool, GitDiffTool, GitLogTool, GitCommitTool,
        GitCreatePrTool, GitBranchTool,
        WebSearchTool, SequentialThinkingTool,
        MemorizeTool, RecallTool, ForgetTool,
    )
    tool_manager.register_tool(DiscoverProjectTool(cwd))
    tool_manager.register_tool(GetFileContentsTool(cwd))
    tool_manager.register_tool(GetFilesInfoTool(cwd))
    tool_manager.register_tool(WriteFileTool(cwd))
    tool_manager.register_tool(DeleteFileTool(cwd))
    tool_manager.register_tool(CreateDirTool(cwd))
    tool_manager.register_tool(ApplyDiffTool(cwd))
    tool_manager.register_tool(EditFileAstTool(cwd))
    tool_manager.register_tool(ListSkillsTool())
    tool_manager.register_tool(SemanticSearchTool(cwd))
    tool_manager.register_tool(GetRepoSkeletonTool(cwd))
    tool_manager.register_tool(QuestionTool())
    tool_manager.register_tool(GitStatusTool(cwd))
    tool_manager.register_tool(GitDiffTool(cwd))
    tool_manager.register_tool(GitLogTool(cwd))
    tool_manager.register_tool(GitCommitTool(cwd))
    tool_manager.register_tool(GitCreatePrTool(cwd))
    tool_manager.register_tool(GitBranchTool(cwd))
    tool_manager.register_tool(WebSearchTool())
    tool_manager.register_tool(SequentialThinkingTool())
    tool_manager.register_tool(MemorizeTool())
    tool_manager.register_tool(RecallTool())
    tool_manager.register_tool(ForgetTool())

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
    
    system_prompt = (
        f"You are Rta, an expert developer CLI assistant. Working in: {cwd}\n"
        f"Project: {json.dumps(project_info)}\n"
        "Rules:\n"
        "- Run shell commands via bash tool, not Python subprocess\n"
        "- Read files with get_file_contents before editing\n"
        "- Verify edits by reading the file back\n"
        "- Use parallel tool execution for independent reads\n"
        "- Ask before destructive ops (deletes, force-push, mass rewrites) via the question tool\n"
        "- Responses stream in real-time — lead with the answer, then details\n"
    )
    
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

            cancel_event = asyncio.Event()
            
            try:
                await tui.handle_events(agent.run_turn(user_input, cancel_event=cancel_event))
            except asyncio.CancelledError:
                console.print("\n[yellow]Interrupted.[/yellow]")
            except KeyboardInterrupt:
                cancel_event.set()
                console.print("\n[yellow]Stopping...[/yellow]")
                await asyncio.sleep(0.1)

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            console.print(f"\n[bold red]Fatal Error:[/bold red] {str(e)}")

    tui.print_summary()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
