"""cmd_auth.py — deprecated stub. Real auth lives in rta_cli.auth."""
# login/logout/whoami/status are top-level `rta` commands now.
# This file kept for backward compat imports only.

from rta_cli.auth import do_login, do_logout, do_whoami, do_status


def auth(args):
    """Legacy dispatcher — prefer 'rta login/logout/whoami/status'."""
    import sys

    if not args:
        print("Usage: rta login | logout | whoami | status", file=sys.stderr)
        sys.exit(1)

    subcmd = args[0]
    dispatch = {
        "login": do_login,
        "logout": do_logout,
        "whoami": do_whoami,
        "status": do_status,
    }
    fn = dispatch.get(subcmd)
    if fn:
        fn()
    else:
        print(f"Unknown subcommand: {subcmd}", file=sys.stderr)
        sys.exit(1)
