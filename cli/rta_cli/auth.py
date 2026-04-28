"""CLI auth flows: login, logout, whoami, status."""
import getpass
import sys

import httpx
from rich.console import Console

from rta_cli.utils import save_credential, load_credential, delete_credential, get_device_id, get_server_url

console = Console()

CLI_VERSION = "0.2.0"


def _headers(api_key: str) -> dict:
    return {
        "X-API-KEY": api_key,
        "X-Device-ID": get_device_id(),
        "X-CLI-Version": CLI_VERSION,
    }


def do_login():
    """Prompt for API key, validate against /v1/auth/me, persist."""
    console.print("[bold #ff3333]Rta Login[/bold #ff3333]")
    console.print(f"[dim]Get your key at [underline]https://rta.sh/dashboard[/underline][/dim]\n")

    for attempt in range(3):
        api_key = getpass.getpass("Enter your Rta API key: ").strip()
        if not api_key:
            console.print("[red]Empty key — try again.[/red]")
            continue

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(
                    f"{get_server_url()}/v1/auth/me",
                    headers=_headers(api_key)
                )
        except httpx.ConnectError:
            console.print("[red]Cannot reach Rta server. Check your connection.[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Network error: {e}[/red]")
            sys.exit(1)

        if resp.status_code == 200:
            data = resp.json()
            email = data.get("email", "unknown")
            tier = data.get("tier", "free")
            save_credential("rta_api_key", api_key)
            console.print(f"\n[bold green]✓ Logged in as {email} ({tier})[/bold green]")
            console.print(f"[dim]Key saved to ~/.rta/credentials[/dim]")
            return
        elif resp.status_code == 401:
            console.print(f"[red]Invalid API key. Try again.[/red]")
        else:
            console.print(f"[red]Server error ({resp.status_code}). Try again later.[/red]")
            sys.exit(1)

    console.print("[red]Too many failed attempts.[/red]")
    sys.exit(1)


def do_logout():
    """Remove stored API key."""
    delete_credential("rta_api_key")
    console.print("[bold green]✓ Logged out. Key removed from ~/.rta/credentials.[/bold green]")


def do_whoami():
    """Show current user info."""
    api_key = load_credential("rta_api_key")
    if not api_key:
        console.print("[red]No API key found. Run: rta login[/red]")
        sys.exit(1)

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{get_server_url()}/v1/auth/me",
                headers=_headers(api_key)
            )
    except Exception as e:
        console.print(f"[red]Network error: {e}[/red]")
        sys.exit(1)

    if resp.status_code == 200:
        data = resp.json()
        console.print(f"[bold #ff3333]User:[/bold #ff3333]  {data.get('email', '?')}")
        console.print(f"[bold #ff3333]Tier:[/bold #ff3333]  {data.get('tier', '?')}")
        console.print(f"[bold #ff3333]ID:[/bold #ff3333]    {data.get('user_id', '?')}")
    elif resp.status_code == 401:
        console.print("[red]Invalid or expired key. Run: rta login[/red]")
        sys.exit(1)
    else:
        console.print(f"[red]Server error ({resp.status_code})[/red]")
        sys.exit(1)


def do_status():
    """Show usage stats."""
    api_key = load_credential("rta_api_key")
    if not api_key:
        console.print("[red]No API key found. Run: rta login[/red]")
        sys.exit(1)

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{get_server_url()}/v1/usage",
                headers=_headers(api_key)
            )
    except Exception as e:
        console.print(f"[red]Network error: {e}[/red]")
        sys.exit(1)

    if resp.status_code == 200:
        d = resp.json()
        tier = d.get("tier", "?")
        calls_today = d.get("calls_today", "?")
        calls_limit = d.get("calls_limit", "?")
        tokens_month = d.get("tokens_used_month", "?")
        tokens_limit = d.get("tokens_limit_month", "?")

        console.print(f"[bold #ff3333]Tier:[/bold #ff3333]         {tier}")
        console.print(f"[bold #ff3333]Calls today:[/bold #ff3333]  {calls_today} / {calls_limit}")
        console.print(f"[bold #ff3333]Tokens/mo:[/bold #ff3333]    {tokens_month} / {tokens_limit}")
    elif resp.status_code == 429:
        console.print(f"[red]Daily limit reached. Upgrade at https://rta.sh/pricing[/red]")
    elif resp.status_code == 401:
        console.print("[red]Invalid or expired key. Run: rta login[/red]")
        sys.exit(1)
    else:
        console.print(f"[red]Server error ({resp.status_code})[/red]")
        sys.exit(1)
