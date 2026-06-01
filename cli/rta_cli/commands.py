import argparse
import os
import sys
from rta_cli.ui import Console

console = Console()

def cd(path: str):
    """Change the tracked workspace"""
    from rta_cli.config import set_last_workspace
    abs_path = os.path.abspath(path)
    if not os.path.isdir(abs_path):
        console.print(f"[bold red]Error: {path} is not a directory.[/bold red]")
        return
    set_last_workspace(abs_path)
    console.print(f"[bold green]Workspace changed to: {abs_path}[/bold green]")

def chat(
    prompt=None,
    clear_context=False,
    workspace=None,
    no_cache=False,
    timeout=120,
    force=False,
    resume=None,
    list_sessions=False,
    privacy=False,
    ollama=None,
):
    """Start the Rta chat interface"""
    if list_sessions:
        from rta_cli.context import list_sessions as ls
        sessions = ls(workspace)
        if not sessions:
            console.print("[yellow]No saved sessions found.[/yellow]")
            return

        console.print("\n[bold]Recent Chat Sessions[/bold]")
        console.print("-" * 60)
        for s in sessions[:15]:
            sid = s['session_id']
            short_id = sid[:8] if len(sid) > 8 else sid
            project = os.path.basename(s['workspace'])
            date = s['display_date']
            console.print(f"ID: [cyan]{short_id}[/] | Project: [green]{project:<15}[/] | Date: {date}")
        console.print("\nRun: [bold]rta chat --resume <ID>[/bold] to continue a session.")
        return

    from rta_cli.chat import RtaChat
    chat_obj = RtaChat(workspace=workspace, session_id=resume, timeout=timeout, force=force, privacy=privacy, ollama=ollama)
    if clear_context or no_cache:
        from rta_cli.context import clear_context as cc
        cc(chat_obj.workspace, session_id=resume)
        if not no_cache:
            chat_obj.messages = []

    chat_obj.run(initial_prompt=prompt)

def ask(
    prompt: str,
    workspace=None,
    resume=None,
    timeout=300,
    force=False,
):
    """Run a one-off agentic request (headless)"""
    from rta_cli.chat import RtaChat
    import json
    chat_obj = RtaChat(workspace=workspace, session_id=resume, timeout=timeout, force=force)
    chat_obj._load_history()
    
    # Add system prompt if needed
    if not chat_obj.messages or not any(m.get("role") == "system" for m in chat_obj.messages):
        system_prompt = f"You are Rta, an expert developer CLI assistant. Working in: {chat_obj.workspace}\n"
        system_prompt += f"Project: {json.dumps(chat_obj.project_info)}\n"
        chat_obj.messages.insert(0, {"role": "system", "content": system_prompt})

    from rta_cli.agent import stream_agent
    
    gen = stream_agent(
        prompt,
        chat_obj.workspace,
        chat_obj.messages,
        chat_obj.provider,
        chat_obj.model,
        session_id=chat_obj.session_id,
        turn_index=chat_obj.turn_index,
        timeout=chat_obj.timeout,
        force=chat_obj.force,
    )
    
    for event in gen:
        if event["type"] == "content":
            print(event["content"], end="", flush=True)
        elif event["type"] == "done":
            chat_obj.messages = event["history"]
            chat_obj.turn_index = event.get("turn_index", chat_obj.turn_index)
            chat_obj._save_history()
            print() # Final newline

def init(project_name: str):
    """Initialize a new project"""
    from rta_cli.cmd_init import init as do_init
    do_init([project_name])

def clone(repo_url: str):
    """Clone a repository"""
    from rta_cli.cmd_clone import clone as do_clone
    do_clone([repo_url])

def login():
    """Authenticate with your Rta API key"""
    from rta_cli.auth import do_login
    do_login()

def logout():
    """Remove stored API key"""
    from rta_cli.auth import do_logout
    do_logout()

def whoami():
    """Show logged-in user info"""
    from rta_cli.auth import do_whoami
    do_whoami()

def status():
    """Show usage stats (calls today, quota left)"""
    from rta_cli.auth import do_status
    do_status()

def update():
    """Check for and install updates"""
    from rta_cli.updater import perform_update
    perform_update()

def skill(args):
    """Manage specialized skills"""
    from rta_cli.skills import list_available_skills, load_skill_content

    if not args.subcommand or args.subcommand == "list":
        skills = list_available_skills()
        if not skills:
            console.print("[yellow]No skills installed. Add folders to ~/.rta/skills/[/yellow]")
            return
        console.print("\n[bold]Installed Skills[/bold]")
        console.print("-" * 60)
        for s in skills:
            console.print(f"[cyan]{s['name']:<15}[/] | {s['description']}")
    elif args.subcommand == "info":
        if not args.name:
            console.print("[red]Error: Skill name required. (rta skill info <name>)[/red]")
            return
        content = load_skill_content(args.name)
        if content:
            console.print(f"\n[bold]Skill: {args.name}[/bold]\n")
            console.print(content)
        else:
            console.print(f"[red]Skill '{args.name}' not found.[/red]")
    elif args.subcommand == "load":
        if not args.name:
            console.print("[red]Error: Skill name required. (rta skill load <name>)[/red]")
            return
        content = load_skill_content(args.name)
        if content:
            # We return the content so chat.py can catch it
            return content
        else:
            console.print(f"[red]Skill '{args.name}' not found.[/red]")

class RtaParser(argparse.ArgumentParser):
    def error(self, message):
        # Catch "invalid choice" errors to handle typos
        import re
        match = re.search(r"invalid choice: '([^']+)'", message)
        if match:
            bad_choice = match.group(1).lower()
            typo_map = {
                "whomai": "whoami",
                "staus": "status",
                "stats": "status",
            }
            if bad_choice in typo_map:
                corrected = typo_map[bad_choice]
                console.print(f"[yellow]Hint: Assuming '{corrected}' instead of '{bad_choice}'[/yellow]")
                # We can't easily restart parsing here without hacky logic, 
                # but we can trigger the intended function directly.
                from rta_cli.auth import do_whoami, do_status
                if corrected == "whoami": do_whoami(); sys.exit(0)
                if corrected == "status": do_status(); sys.exit(0)

        console.print(f"[bold red]Error: {message}[/bold red]")
        self.print_help()
        sys.exit(2)

def main():
    parser = RtaParser(
        prog="rta",
        description="Rta - AI-assisted code editor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Global options
    parser.add_argument("--clear-context", action="store_true", help="Clear chat history")
    parser.add_argument("--workspace", help="Working directory")
    parser.add_argument("--no-cache", action="store_true", help="Ignore context")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout for shell commands in seconds")
    parser.add_argument("--force", action="store_true", help="Skip destructive action confirmations")
    parser.add_argument("--resume", help="Resume a previous session by ID")
    parser.add_argument("--list-sessions", action="store_true", help="List previous chat sessions")
    parser.add_argument("--privacy", action="store_true", help="Hide email in header")
    parser.add_argument("--legacy", action="store_true", help="Use the legacy UI core")
    parser.add_argument("--version", action="store_true", help="Show version info")
    parser.add_argument("--ollama", nargs="?", const="deepseek-r1", help="Use local Ollama model (default: deepseek-r1)")
    
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # cd
    p_cd = subparsers.add_parser("cd", help="Change the tracked workspace")
    p_cd.add_argument("path", help="Path to the new workspace")

    # chat
    p_chat = subparsers.add_parser("chat", help="Start the Rta chat interface")
    p_chat.add_argument("prompt", nargs="?", help="Initial prompt for the chat")
    p_chat.add_argument("--clear-context", action="store_true", help="Clear chat history")
    p_chat.add_argument("--workspace", help="Working directory")
    p_chat.add_argument("--no-cache", action="store_true", help="Ignore context")
    p_chat.add_argument("--timeout", type=int, default=120, help="Timeout for shell commands in seconds")
    p_chat.add_argument("--force", action="store_true", help="Skip destructive action confirmations")
    p_chat.add_argument("--resume", help="Resume a previous session by ID")
    p_chat.add_argument("--list-sessions", action="store_true", help="List previous chat sessions")
    p_chat.add_argument("--privacy", action="store_true", help="Hide email in header")
    p_chat.add_argument("--legacy", action="store_true", help="Use the legacy UI core")

    # ask
    p_ask = subparsers.add_parser("ask", help="Run a one-off agentic request (headless)")
    p_ask.add_argument("prompt", help="Prompt for the agent")
    p_ask.add_argument("--workspace", help="Working directory")
    p_ask.add_argument("--resume", help="Resume a previous session by ID")
    p_ask.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    p_ask.add_argument("--force", action="store_true", help="Skip confirmation")

    # init
    p_init = subparsers.add_parser("init", help="Initialize a new project")
    p_init.add_argument("project_name", help="Name of the project to create")

    # clone
    p_clone = subparsers.add_parser("clone", help="Clone a repository")
    p_clone.add_argument("repo_url", help="Repository URL to clone")

    # skill
    p_skill = subparsers.add_parser("skill", help="Manage specialized skills")
    p_skill.add_argument("subcommand", nargs="?", choices=["list", "info", "load"], default="list")
    p_skill.add_argument("name", nargs="?", help="Skill name for 'info' or 'load' command")

    # auth commands
    subparsers.add_parser("login", help="Authenticate with your Rta API key")
    subparsers.add_parser("logout", help="Remove stored API key")
    subparsers.add_parser("whoami", help="Show logged-in user info")
    subparsers.add_parser("status", help="Show usage stats (calls today, quota left)")
    subparsers.add_parser("update", help="Check for and install updates")

    # Parse arguments
    args, unknown = parser.parse_known_args()
    known_vars = vars(args)

    # Handle global flags first
    if known_vars.get("version"):
        from rta_cli.chat import ASCII_ART
        print(ASCII_ART)
        print("Rta CLI v0.5.0")
        return

    if args.command == "login":
        return login()
    if args.command == "logout":
        return logout()
    if args.command == "whoami":
        return whoami()
    if args.command == "status":
        return status()
    if args.command == "update":
        return update()
    if args.command == "cd":
        return cd(args.path)
    elif args.command == "chat":
        if not known_vars.get("legacy"):
            from rta_cli.main_async import main as run_modern
            return run_modern(args)
        return chat(
            prompt=args.prompt,
            clear_context=args.clear_context,
            workspace=args.workspace,
            no_cache=args.no_cache,
            timeout=args.timeout,
            force=args.force,
            resume=args.resume,
            list_sessions=args.list_sessions,
            privacy=args.privacy,
            ollama=args.ollama
        )
    elif args.command == "ask":
        return ask(
            prompt=args.prompt,
            workspace=args.workspace,
            resume=args.resume,
            timeout=args.timeout,
            force=args.force
        )
    elif args.command == "init":
        return init(args.project_name)
    elif args.command == "clone":
        return clone(args.repo_url)
    elif args.command == "skill":
        return skill(args)
    elif args.command is None:
        # Default behavior: chat
        if unknown:
            for arg in unknown:
                if arg.startswith("-"):
                    # Check for common typos or misplaced flags
                    raw_name = arg.lstrip("-").lower()
                    # Map common typos
                    typo_map = {
                        "whomai": "whoami",
                        "whoami": "whoami",
                        "status": "status",
                        "login": "login",
                        "logout": "logout",
                        "init": "init",
                        "chat": "chat",
                        "ask": "ask",
                        "clone": "clone"
                    }
                    
                    if raw_name in typo_map:
                        cmd_name = typo_map[raw_name]
                        console.print(f"[yellow]Hint: Executing 'rta {cmd_name}' (matched from '{arg}')[/yellow]")
                        if cmd_name == "whoami": return whoami()
                        if cmd_name == "status": return status()
                        if cmd_name == "login": return login()
                        if cmd_name == "logout": return logout()
                        if cmd_name == "init": return init(None) # Needs args handling usually
                    
                    if arg.startswith("--"):
                        console.print(f"[bold red]Error: Unknown option {arg}[/bold red]")
                        parser.print_help()
                        return

        if not hasattr(args, "prompt") or not args.prompt:
            args.prompt = " ".join(unknown) if unknown else None

        if not known_vars.get("legacy"):
            from rta_cli.main_async import main as run_modern
            return run_modern(args)

        prompt = " ".join(unknown) if unknown else None
        return chat(
            prompt=prompt,
            clear_context=known_vars.get("clear_context"),
            workspace=known_vars.get("workspace"),
            no_cache=known_vars.get("no_cache"),
            timeout=known_vars.get("timeout", 120),
            force=known_vars.get("force"),
            resume=known_vars.get("resume"),
            list_sessions=known_vars.get("list_sessions"),
            privacy=known_vars.get("privacy"),
            ollama=known_vars.get("ollama")
        )
    else:
        console.print(f"[bold red]Error: Unknown command {args.command}[/bold red]")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
