"""CLI auth flows: login, logout, whoami, status."""

import getpass
import sys

import httpx
from rta_cli.ui import Console

from rta_cli.utils import (
    save_credential,
    load_credential,
    delete_credential,
    get_device_id,
    get_server_url,
)

console = Console()

CLI_VERSION = "0.5.0"


def _headers(api_key: str) -> dict:
    return {
        "X-API-KEY": api_key,
        "X-Device-ID": get_device_id(),
        "X-CLI-Version": CLI_VERSION,
        "User-Agent": "rta-cli/1.0",
    }


def do_login():
    """Prompt for API key, validate against /v1/auth/me, persist."""
    console.print("[bold #ff3333]Rta Login[/bold #ff3333]")
    console.print(
        "[dim]Get your key at [underline]https://rta-three.vercel.app/dashboard.html[/underline][/dim]\n"
    )

    for attempt in range(3):
        api_key = getpass.getpass("Enter your Rta API key: ").strip()
        if not api_key:
            console.print("[red]Empty key — try again.[/red]")
            continue

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(
                    f"{get_server_url()}/v1/auth/me", headers=_headers(api_key)
                )
        except httpx.ConnectError:
            console.print("[red]Cannot reach Rta server. Check your connection.[/red]")
            sys.exit(1)
        except Exception as e:
            import traceback

            traceback.print_exc()
            console.print(f"[red]Network error: {e}[/red]")
            sys.exit(1)

        if resp.status_code == 200:
            data = resp.json()
            tier = data.get("tier", "free")
            save_credential("rta_api_key", api_key)
            console.print(f"\n[bold green]✓ Authenticated ({tier})[/bold green]")
            console.print("[dim]Key saved to ~/.rta/credentials[/dim]")
            return
        elif resp.status_code == 401:
            console.print("[red]Invalid API key. Try again.[/red]")
        else:
            console.print(
                f"[red]Server error ({resp.status_code}). Try again later.[/red]"
            )
            sys.exit(1)

    console.print("[red]Too many failed attempts.[/red]")
    sys.exit(1)


def do_logout():
    """Remove stored API key."""
    delete_credential("rta_api_key")
    console.print(
        "[bold green]✓ Logged out. Key removed from ~/.rta/credentials.[/bold green]"
    )


def do_whoami():
    """Show current user info."""
    api_key = load_credential("rta_api_key")
    if not api_key:
        console.print("[red]No API key found. Run: rta login[/red]")
        sys.exit(1)

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{get_server_url()}/v1/auth/me", headers=_headers(api_key)
            )
    except Exception as e:
        console.print(f"[red]Network error: {e}[/red]")
        sys.exit(1)

    if resp.status_code == 200:
        data = resp.json()
        console.print("[bold #ff3333]Status:[/bold #ff3333] Authenticated")
        console.print(f"[bold #ff3333]Tier:[/bold #ff3333]   {data.get('tier', '?')}")
        console.print(
            f"[bold #ff3333]ID:[/bold #ff3333]     {data.get('user_id', '?')}"
        )
    elif resp.status_code == 401:
        console.print("[red]Invalid or expired key. Run: rta login[/red]")
        sys.exit(1)
    else:
        console.print(f"[red]Server error ({resp.status_code})[/red]")
        sys.exit(1)


def do_status():
    """Show usage stats."""
    import time as _time

    api_key = load_credential("rta_api_key")
    if not api_key:
        console.print("[red]No API key found. Run: rta login[/red]")
        sys.exit(1)

    # Measure ping
    ping_start = _time.monotonic()
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{get_server_url()}/v1/usage", headers=_headers(api_key))
    except Exception as e:
        console.print(f"[red]Network error: {e}[/red]")
        sys.exit(1)
    ping_ms = round((_time.monotonic() - ping_start) * 1000)

    if resp.status_code == 200:
        d = resp.json()
        tier = d.get("tier", "?")
        calls_today = d.get("calls_today", "?")
        calls_limit = d.get("calls_limit", "?")
        tokens_today = d.get("tokens_today", "?")
        tokens_limit_day = d.get("tokens_limit_day", "?")
        tokens_month = d.get("tokens_used_month", "?")
        tokens_limit = d.get("tokens_limit_month", "?")

        server = get_server_url().replace("https://", "").replace("http://", "")
        console.print(f"[bold #ff3333]Server:[/bold #ff3333]       {server}")
        console.print(f"[bold #ff3333]Ping:[/bold #ff3333]         {ping_ms}ms")
        console.print(f"[bold #ff3333]Tier:[/bold #ff3333]         {tier}")
        console.print(
            f"[bold #ff3333]Calls today:[/bold #ff3333]  {calls_today} / {calls_limit}"
        )
        console.print(
            f"[bold #ff3333]Tokens today:[/bold #ff3333] {tokens_today} / {tokens_limit_day}"
        )
        console.print(
            f"[bold #ff3333]Tokens/mo:[/bold #ff3333]    {tokens_month} / {tokens_limit}"
        )
    elif resp.status_code == 429:
        console.print(
            "[red]Daily limit reached. Upgrade at https://rta-three.vercel.app/#/pricing[/red]"
        )
    elif resp.status_code == 401:
        console.print("[red]Invalid or expired key. Run: rta login[/red]")
        sys.exit(1)
    else:
        console.print(f"[red]Server error ({resp.status_code})[/red]")
        sys.exit(1)
