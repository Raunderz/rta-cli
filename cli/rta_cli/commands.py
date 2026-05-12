import typer
import os
from rta_cli.ui import Console

app = typer.Typer(
    name="rta",
    help="AI-assisted code editor CLI",
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
console = Console()


@app.command()
def cd(path: str = typer.Argument(..., help="Path to the new workspace")):
    """Change the tracked workspace"""
    from rta_cli.config import set_last_workspace
    abs_path = os.path.abspath(path)
    if not os.path.isdir(abs_path):
        console.print(f"[bold red]Error: {path} is not a directory.[/bold red]")
        return
    set_last_workspace(abs_path)
    console.print(f"[bold green]Workspace changed to: {abs_path}[/bold green]")


@app.command()
def chat(
    prompt: str = typer.Argument(None, help="Initial prompt for the chat"),
    clear_context: bool = typer.Option(False, "--clear-context", help="Clear chat history"),
    workspace: str = typer.Option(None, "--workspace", help="Working directory"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignore context"),
    timeout: int = typer.Option(120, "--timeout", help="Timeout for shell commands in seconds"),
    force: bool = typer.Option(False, "--force", help="Skip destructive action confirmations"),
    resume: str = typer.Option(None, "--resume", help="Resume a previous session by ID"),
    list_sessions: bool = typer.Option(False, "--list-sessions", help="List previous chat sessions"),
    privacy: bool = typer.Option(False, "--privacy", help="Hide email in header"),
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

    if prompt:
        # Run a single turn or start chat with prompt
        chat_obj.run(initial_prompt=prompt)
    else:
        chat_obj.run()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    clear_context: bool = typer.Option(False, "--clear-context", help="Clear chat history"),
    workspace: str = typer.Option(None, "--workspace", help="Working directory"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignore context"),
    timeout: int = typer.Option(120, "--timeout", help="Timeout for shell commands in seconds"),
    force: bool = typer.Option(False, "--force", help="Skip destructive action confirmations"),
    resume: str = typer.Option(None, "--resume", help="Resume a previous session by ID"),
    list_sessions: bool = typer.Option(False, "--list-sessions", help="List previous chat sessions"),
    privacy: bool = typer.Option(False, "--privacy", help="Hide email in header"),
):
    """Rta - AI-assisted code editor CLI"""
    if ctx.invoked_subcommand is None:
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
            return

        from rta_cli.chat import RtaChat
        chat_obj = RtaChat(workspace=workspace, session_id=resume, timeout=timeout, force=force, privacy=privacy)
        
        if clear_context or no_cache:
            from rta_cli.context import clear_context as cc
            cc(chat_obj.workspace, session_id=resume)
            if not no_cache:
                chat_obj.messages = []

        prompt = " ".join(ctx.args) if ctx.args else None
        chat_obj.run(initial_prompt=prompt)


@app.command()
def init(project_name: str = typer.Argument(..., help="Name of the project to create")):
    """Initialize a new project"""
    from rta_cli.cmd_init import init as do_init
    do_init([project_name])


@app.command()
def clone(repo_url: str = typer.Argument(..., help="Repository URL to clone")):
    """Clone a repository"""
    from rta_cli.cmd_clone import clone as do_clone
    do_clone([repo_url])


@app.command()
def login():
    """Authenticate with your Rta API key"""
    from rta_cli.auth import do_login
    do_login()


@app.command()
def logout():
    """Remove stored API key"""
    from rta_cli.auth import do_logout
    do_logout()


@app.command()
def whoami():
    """Show logged-in user info"""
    from rta_cli.auth import do_whoami
    do_whoami()


@app.command()
def status():
    """Show usage stats (calls today, quota left)"""
    from rta_cli.auth import do_status
    do_status()


if __name__ == "__main__":
    app()
