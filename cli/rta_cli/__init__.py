"""Rta CLI - Minimal, fast."""

__version__ = "0.5.0"


def main():
    """Entry point for rta CLI, used by the console script and standalone binary."""
    from rta_cli.commands import main as do_main

    do_main()


if __name__ == "__main__":
    main()
