"""Rta CLI - Minimal, fast."""

__version__ = "0.1.0"


def main():
    """Entry point for rta CLI, used by the console script and standalone binary."""
    from rta_cli.commands import app
    app()
