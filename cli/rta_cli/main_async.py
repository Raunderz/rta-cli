import asyncio
import json
import sys
import time
import os
try:
    import readline
except ImportError:
    pass
from pathlib import Path
from rich.console import Console
from rta_cli.chat import ASCII_ART
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

console = Console()

global_provider = None

async def handle_slash_command(user_input: str, provider=None) -> bool:
    global global_provider
    if provider:
        global_provider = provider
    
    if not user_input.startswith("/"):
        return False
    parts = user_input[1:].split()
    if not parts:
        return False
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "help":
        console.print("\n[bold #ff3333]Available Commands:[/bold #ff3333]")
        console.print("  /clear         - Clear chat history & screen")
        console.print("  /exit          - Exit the chat")
        console.print("  /thinkmode     - Toggle Ollama thinking mode (on/off)")
        console.print("  /models        - List and select local Ollama models")
        console.print("\n[dim]You can also run any Rta CLI command here (e.g., /status, /whoami)[/dim]\n")
        return True

    if cmd == "thinkmode":
        if hasattr(global_provider, "think"):
            global_provider.think = not global_provider.think
            status = "enabled" if global_provider.think else "disabled"
            console.print(f"[bold green]Ollama thinking mode {status}.[/bold green]")
        else:
            console.print("[yellow]Thinking mode only supported for local Ollama.[/yellow]")
        return True

    if cmd == "models":
        if hasattr(global_provider, "list_models"):
            models = await global_provider.list_models()
            if not models:
                console.print("[red]No local Ollama models found.[/red]")
            else:
                console.print("\n[bold]Available Ollama Models:[/bold]")
                for i, m in enumerate(models):
                    console.print(f"  {i+1}. {m}")
                try:
                    # In async context, console.input (rich) is blocking but usually OK for REPL.
                    # For a truly async-safe input we'd need more, but this fixes the loop error.
                    choice = console.input("\nSelect model number (or press Enter to cancel): ")
                    if choice.strip():
                        idx = int(choice) - 1
                        if 0 <= idx < len(models):
                            global_provider.model = models[idx]
                            console.print(f"[bold green]Switched to model: {global_provider.model}[/bold green]")
                except (ValueError, IndexError):
                    console.print("[red]Invalid selection.[/red]")
        else:
            console.print("[yellow]Model selection only supported for local Ollama.[/yellow]")
        return True

    if cmd in ("clear", "cls"):
        os.system("cls" if os.name == "nt" else "clear")
        return True

    if cmd == "exit":
        return False

    try:
        from rta_cli.commands import main as rta_main
        orig_argv = sys.argv
        sys.argv = ["rta", cmd] + args
        rta_main()
        sys.argv = orig_argv
    except SystemExit:
        pass
    return True

async def async_main(args=None):
    console = Console()
    console.print(f"[bold red]{ASCII_ART}[/bold red]")
    console.print("[bold green]Rta CLI v0.5.0[/bold green]")

    # 1. Setup Core Components
    if args and args.ollama:
        from .core.provider import OllamaProvider
        provider = OllamaProvider(model=args.ollama)
    else:
        provider = AsyncRtaProvider()
    
    # Use workspace from args if provided
    cwd = args.workspace if (args and args.workspace) else os.getcwd()
    if not os.path.isabs(cwd):
        cwd = os.path.abspath(cwd)
    
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
        WebSearchTool, FetchUrlTool, ArxivSearchTool, SoSearchTool, SequentialThinkingTool,
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
    tool_manager.register_tool(FetchUrlTool())
    tool_manager.register_tool(ArxivSearchTool())
    tool_manager.register_tool(SoSearchTool())
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

    session_dir = Path.home() / ".rta" / "sessions"
    session_manager = SessionManager(session_dir)
    
    if args and args.list_sessions:
        sessions = session_manager.list_sessions()
        if not sessions:
            console.print("[dim]No previous sessions found.[/dim]")
        else:
            console.print("\n[bold]Previous Sessions:[/bold]")
            for s in sessions:
                print(f"  {s['id']} - {s['timestamp']} ({s['turns']} turns)")
        return

    current_session_id = args.resume if (args and args.resume) else session_manager.current_session_id

    if args and args.clear_context:
        session_manager.clear()
        console.print("[dim]Chat history cleared.[/dim]")
    
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
    if args and hasattr(args, "prompt") and args.prompt:
        # Handle initial prompt if passed
        user_input = args.prompt
        tui.track_input(user_input)
        cancel_event = asyncio.Event()
        await tui.handle_events(agent.run_turn(
            user_input, 
            session_id=current_session_id, 
            model=getattr(provider, "model", None),
            cancel_event=cancel_event
        ))
        # After initial prompt, we might want to continue to REPL
    
    while True:
        try:
            user_input = console.input("\n[bold cyan]rta>[/bold cyan] ")
            if not user_input.strip():
                continue

            if user_input.startswith("/"):
                if not await handle_slash_command(user_input, provider=provider):
                    break
                continue

            tui.track_input(user_input)
            cancel_event = asyncio.Event()
            
            try:
                await tui.handle_events(agent.run_turn(
                    user_input, 
                    session_id=current_session_id, 
                    model=getattr(provider, "model", None),
                    cancel_event=cancel_event
                ))
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

def main(args=None):
    asyncio.run(async_main(args))

if __name__ == "__main__":
    main()
