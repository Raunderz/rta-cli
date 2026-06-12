import argparse
import asyncio

from kon import config

from .llm import PROVIDER_API_BY_NAME
from .version import VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rta")
    parser.add_argument("--model", "-m", help="Model to use")
    parser.add_argument("--provider", choices=sorted(PROVIDER_API_BY_NAME), help="Provider to use")
    parser.add_argument(
        "--prompt",
        "-p",
        nargs="?",
        const="-",
        default=None,
        help="Run a single prompt non-interactively, then exit "
        "(omit the value or pipe stdin to read the prompt from stdin)",
    )
    parser.add_argument("--base-url", "-u", help="Base URL for API")
    parser.add_argument(
        "--openai-compat-auth",
        choices=("auto", "required", "none"),
        help="Auth mode for OpenAI-compatible endpoints",
    )
    parser.add_argument(
        "--anthropic-compat-auth",
        choices=("auto", "required", "none"),
        help="Auth mode for Anthropic-compatible endpoints",
    )
    parser.add_argument(
        "--insecure-skip-verify",
        action="store_true",
        help="Skip TLS verification (e.g. self-signed certs on local providers)",
    )
    parser.add_argument(
        "--continue",
        "-c",
        action="store_true",
        dest="continue_recent",
        help="Resume the most recent session",
    )
    parser.add_argument(
        "--resume",
        "-r",
        dest="resume_session",
        help="Resume a specific session by ID (full or unique prefix)",
    )
    parser.add_argument("--version", action="version", version=f"rta {VERSION}")
    parser.add_argument(
        "--extra-tools", help="Comma-separated extra tools to enable (e.g. web_search,web_fetch)"
    )
    return parser


import argparse
import asyncio
import logging
import os
import sys

from kon import config

from .llm import PROVIDER_API_BY_NAME
from .version import VERSION

def setup_logging():
    """Initializes logging to file in ~/.rta/kon.log"""
    log_dir = os.path.expanduser("~/.rta")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "kon.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8")
        ]
    )
    logger = logging.getLogger("kon")
    logger.info(f"--- Rta {VERSION} starting ---")

def main() -> None:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    if args.prompt is not None and (args.continue_recent or args.resume_session):
        parser.error("-c/--continue and -r/--resume are not supported with -p/--prompt")

    if args.insecure_skip_verify:
        print("Warning: TLS verification disabled (--insecure-skip-verify)", file=sys.stderr)
        config.llm.tls.insecure_skip_verify = True

    extra_tools = (
        [t.strip() for t in args.extra_tools.split(",") if t.strip()] if args.extra_tools else None
    )

    if args.prompt is not None:
        from .headless import run_headless

        try:
            raise SystemExit(
                asyncio.run(
                    run_headless(
                        prompt_arg=args.prompt,
                        model=args.model,
                        provider=args.provider,
                        base_url=args.base_url,
                        openai_compat_auth_mode=args.openai_compat_auth,
                        anthropic_compat_auth_mode=args.anthropic_compat_auth,
                        extra_tools=extra_tools,
                    )
                )
            )
        except Exception as e:
            logging.getLogger("kon").error(f"Headless error: {e}", exc_info=True)
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    from .ui.app import run_tui

    try:
        run_tui(args, extra_tools=extra_tools)
    except FileNotFoundError as e:
        # Specifically handle session not found for --resume/--continue
        if args.resume_session or args.continue_recent:
            print(f"Error: Session not found ({e})", file=sys.stderr)
            sys.exit(1)
        raise
    except Exception as e:
        logging.getLogger("kon").error(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}", file=sys.stderr)
        print("See ~/.rta/kon.log for details.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
