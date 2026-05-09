import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="rta",
    help="AI-assisted code editor CLI",
    add_completion=False,
)
console = Console()


@app.command()
def chat(
    prompt: str = typer.Argument(None, help="Initial prompt for the chat"),
    clear_context: bool = typer.Option(False, "--clear-context", help="Clear chat history"),
    workspace: str = typer.Option(None, "--workspace", help="Working directory"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignore context"),
    timeout: int = typer.Option(120, "--timeout", help="Timeout for shell commands in seconds"),
):
    """Start the Rta chat interface"""
    from rta_cli.chat import RtaChat
    chat_obj = RtaChat(workspace=workspace, timeout=timeout)
    
    if clear_context or no_cache:
        from rta_cli.context import clear_context as cc
        cc(chat_obj.workspace)
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
    prompt: str = typer.Argument(None, help="Initial prompt for the chat"),
    clear_context: bool = typer.Option(False, "--clear-context", help="Clear chat history"),
    workspace: str = typer.Option(None, "--workspace", help="Working directory"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignore context"),
    timeout: int = typer.Option(120, "--timeout", help="Timeout for shell commands in seconds"),
):
    """Rta - AI-assisted code editor CLI"""
    if ctx.invoked_subcommand is None:
        from rta_cli.chat import RtaChat
        chat_obj = RtaChat(workspace=workspace, timeout=timeout)
        
        if clear_context or no_cache:
            from rta_cli.context import clear_context as cc
            cc(chat_obj.workspace)
            if not no_cache:
                chat_obj.messages = []

        chat_obj.run(initial_prompt=prompt)


@app.command()
def init():
    """Initialize a new project"""
    from rta_cli.cmd_init import init
    init([])


@app.command()
def clone():
    """Clone a repository"""
    from rta_cli.cmd_clone import clone
    clone([])


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
