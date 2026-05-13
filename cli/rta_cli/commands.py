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
    chat_obj = RtaChat(workspace=workspace, session_id=resume, timeout=timeout, force=force, privacy=privacy)
    
    if clear_context or no_cache:
        from rta_cli.context import clear_context as cc
        cc(chat_obj.workspace, session_id=resume)
        if not no_cache:
            chat_obj.messages = []

    chat_obj.run(initial_prompt=prompt)

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
        console.print(f"[bold red]Error: {message}[/bold red]")
        self.print_help()
        sys.exit(2)

def main():
    parser = RtaParser(
        prog="rta",
        description="Rta - AI-assisted code editor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Global options for chat (default command)
    parser.add_argument("--clear-context", action="store_true", help="Clear chat history")
    parser.add_argument("--workspace", help="Working directory")
    parser.add_argument("--no-cache", action="store_true", help="Ignore context")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout for shell commands in seconds")
    parser.add_argument("--force", action="store_true", help="Skip destructive action confirmations")
    parser.add_argument("--resume", help="Resume a previous session by ID")
    parser.add_argument("--list-sessions", action="store_true", help="List previous chat sessions")
    parser.add_argument("--privacy", action="store_true", help="Hide email in header")
    
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

    # Parse arguments
    # If we have unknown args, they might be for the prompt if we didn't specify a command
    args, unknown = parser.parse_known_args()

    if args.command == "cd":
        cd(args.path)
    elif args.command == "chat":
        chat(
            prompt=args.prompt,
            clear_context=args.clear_context,
            workspace=args.workspace,
            no_cache=args.no_cache,
            timeout=args.timeout,
            force=args.force,
            resume=args.resume,
            list_sessions=args.list_sessions,
            privacy=args.privacy
        )
    elif args.command == "init":
        init(args.project_name)
    elif args.command == "clone":
        clone(args.repo_url)
    elif args.command == "skill":
        skill(args)
    elif args.command == "login":
        login()
    elif args.command == "logout":
        logout()
    elif args.command == "whoami":
        whoami()
    elif args.command == "status":
        status()
    else:
        # Default behavior: chat
        prompt = " ".join(unknown) if unknown else None
        chat(
            prompt=prompt,
            clear_context=args.clear_context,
            workspace=args.workspace,
            no_cache=args.no_cache,
            timeout=args.timeout,
            force=args.force,
            resume=args.resume,
            list_sessions=args.list_sessions,
            privacy=args.privacy
        )

if __name__ == "__main__":
    main()
