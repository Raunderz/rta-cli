"""Rta CLI - Minimal, fast."""

__version__ = "0.1.0"


def main():
    """Entry point for rta CLI, used by the console script and standalone binary."""
    import sys
    
    # List of known subcommands to avoid intercepting them
    commands = ["cd", "chat", "init", "clone", "login", "logout", "whoami", "status"]
    
    # If the first argument looks like a prompt (not a command and not an option),
    # insert 'chat' as the subcommand.
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        # Check if it's a known command or if it starts with '-' (option)
        if arg not in commands and not arg.startswith("-"):
            # Insert 'chat' at index 1 so it becomes 'rta chat <prompt>'
            sys.argv.insert(1, "chat")

    from rta_cli.commands import app
    app()


if __name__ == "__main__":
    main()
