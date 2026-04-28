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
def chat():
    """Start the Rta chat interface"""
    from rta_cli.chat import start_chat
    start_chat()


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """Rta - AI-assisted code editor CLI"""
    if ctx.invoked_subcommand is None:
        from rta_cli.chat import start_chat
        start_chat()


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
