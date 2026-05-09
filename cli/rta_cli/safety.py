import os
import sys

from rta_cli.ui import Console
console = Console()


_active_status = None


def set_active_status(status):
    global _active_status
    _active_status = status


def confirm_destructive(action, path, force=False):
    if force:
        return True

    msg = {
        "delete_file": f"Delete {path}?",
        "delete_dir": f"Delete {path} and contents?",
        "run_dangerous": f"Run potentially dangerous command?",
    }.get(action, f"Confirm {action}?")

    global _active_status
    if _active_status:
        _active_status.stop()

    try:
        response = console.input(
            f"\n[bold red]\u26a0 WARNING:[/bold red] {msg}\n"
            f"[yellow]Type 'yes' to confirm, 'no' to cancel: [/yellow]"
        )
        return response.lower().strip() in ("yes", "y")
    except (KeyboardInterrupt, EOFError):
        return False
    finally:
        if _active_status:
            _active_status.start()


def is_dangerous_command(command):
    dangerous_patterns = [
        "rm -rf",
        "rm -r",
        "del /f",
        "del /s",
        "format ",
        "mkfs",
        "dd ",
        "> /dev/sd",
        ":(){ :|:& };:",
        "chmod -R 777",
        "chown -R",
    ]
    cmd_clean = command.lower().strip()
    for pattern in dangerous_patterns:
        if pattern in cmd_clean:
            return True
    return False