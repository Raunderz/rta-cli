import os
import sys
import time
import signal
import subprocess
import json
import random
try:
    import readline
    # Suppress potential rl_print_keybinding warning from some readline/sh environments
    if hasattr(readline, 'parse_and_bind'):
        try:
            readline.parse_and_bind("tab: complete")
        except Exception:
            pass
except (ImportError, AttributeError):
    pass # Windows or incomplete readline install

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.markdown import Markdown

console = Console()

ASCII_ART = r""" _  .-')   .-') _      ('-.     
( \( -O ) (  OO) )    ( OO ).-. 
 ,------. /     '._   / . --. / 
 |   /`. '|'--...__)  | \-.  \  
 |  /  | |'--.  .--'.-'-'  |  | 
 |  |_.' |   |  |    \| |_.'  | 
 |  .  '.'   |  |     |  .-.  | 
 |  |\  \    |  |     |  | |  | 
 `--' '--'   `--'     `--' `--' """

LOADING_MESSAGES = [
    "Navigating the codebase...",
    "Herding electrons...",
    "Consulting the silicon gods...",
    "Decrypting spaghetti code...",
    "Optimizing orbits...",
    "Refactoring the universe...",
    "Avoiding infinite loops...",
    "Polishing pixels...",
    "Chasing segment faults...",
    "Compiling thoughts...",
    "Summoning the logic...",
    "Rewriting the future...",
    "Chasing bugs in the dark...",
    "Parsing complexity...",
    "Thinking in 4 Dimensions...",
    "Looks stuck ? It probably isn't"
]

class RtaChat:
    def __init__(self, workspace=None, session_id=None, timeout=120, force=False):
        self.last_ctrl_c = 0
        
        from rta_cli.config import get_last_workspace, set_last_workspace
        if workspace:
            self.workspace = os.path.abspath(workspace)
        else:
            # If current dir is not a git repo or something, maybe use last workspace?
            # Actually, standard behavior: use current dir if it looks like a project, 
            # otherwise fallback to last workspace.
            # For now, let's just prioritize provided > last > current.
            last = get_last_workspace()
            if last and not os.path.exists(".git") and not os.path.exists("package.json"):
                self.workspace = last
            else:
                self.workspace = os.path.abspath(os.getcwd())
        
        set_last_workspace(self.workspace)
        self.workspace_name = os.path.basename(self.workspace)
        self.version = "v0.2.0"
        self.ascii_art = ASCII_ART
        self.timeout = timeout
        self.force = force

        # Project Discovery on startup
        from rta_cli.discovery import discover_project
        self.project_info = discover_project(self.workspace)

        from rta_cli.utils import load_credential
        api_key = load_credential("rta_api_key")
        if not api_key:
            console.print("[bold red]No API key found. Run: rta login[/bold red]")
            sys.exit(1)
        self.user = "authenticated"
        try:
            from rta_cli.utils import get_server_url, get_device_id
            import httpx
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{get_server_url()}/v1/auth/me", headers={
                    "X-API-KEY": api_key,
                    "X-Device-ID": get_device_id(),
                    "X-CLI-Version": "0.2.0",
                    "ngrok-skip-browser-warning": "69420",
                    "User-Agent": "rta-cli/1.0"
                })
                if res.status_code == 200:
                    self.user = res.json().get("email", "authenticated")
        except:
            pass

        if hasattr(sys, '_MEIPASS'):
            self.config_path = os.path.join(sys._MEIPASS, 'rta_cli', 'config.json')
        else:
            self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')

        self.provider = "rta"
        self.model = "auto"

        self.messages = []
        self.rta_dir = os.path.join(self.workspace, ".rta")
        self.history_path = os.path.join(self.rta_dir, "history.json")

        import uuid
        self.session_id = session_id or str(uuid.uuid4())
        self.turn_index = 0

        self.start_mem = self._get_memory_usage()
        self.session_usage = {"input": 0, "output": 0, "total": 0, "cached": 0, "start_time": time.time()}

    def _get_memory_usage(self):
        try:
            if os.path.exists('/proc/self/status'):
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            return f"{int(line.split()[1]) / 1024:.1f} MB"
            return "N/A"
        except:
            return "N/A"

    def _load_history(self):
        from rta_cli.context import load_context
        msgs, sid = load_context(workspace_dir=self.workspace, session_id=self.session_id, max_turns=10)
        self.messages = msgs
        if sid:
            self.session_id = sid
            # Calculate turn index based on message count
            # Each pair is 2 messages + tool messages. 
            # Simple heuristic: total non-system messages
            self.turn_index = sum(1 for m in self.messages if m.get("role") != "system")

    def _save_history(self):
        from rta_cli.context import save_context
        save_context(self.workspace, self.session_id, self.messages)

    def _trim_messages(self, max_msgs=20):
        """Aggressively prune and truncate history to keep payloads small."""
        if len(self.messages) > max_msgs:
            # Preserve system prompt if present at index 0
            if self.messages and self.messages[0].get("role") == "system":
                system_msg = self.messages[0]
                # Keep system prompt + last N-1 messages
                self.messages = [system_msg] + self.messages[-(max_msgs-1):]
            else:
                self.messages = self.messages[-max_msgs:]
        
        for msg in self.messages:
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 20000:
                msg["content"] = content[:20000] + "\n[... CONTENT TRUNCATED BY CLI ...]"
            
            # Also handle tool result parts if they exist (for some providers)
            if msg.get("role") == "function" or msg.get("role") == "tool":
                if isinstance(content, str) and len(content) > 15000:
                    msg["content"] = content[:15000] + "\n[... TOOL RESULT TRUNCATED ...]"

    def print_header(self):
        ascii_lines = self.ascii_art.splitlines()
        styled_ascii = Text()
        for i, line in enumerate(ascii_lines):
            color = f"#{max(50, 200 - i*20):02x}0000"
            styled_ascii.append(line + "\n", style=f"bold {color}")
        
        info_text = Text()
        info_text.append(f"\n   Rta Cli {self.version}\n", style="bold #ff3333")
        info_text.append(f"   User:     ", style="#880000")
        info_text.append(f"{self.user}\n", style="#cc0000")
        info_text.append(f"   Provider: ", style="#880000")
        info_text.append(f"{self.provider}\n", style="#cc0000")
        info_text.append(f"   Model:    ", style="#880000")
        info_text.append(f"{self.model}\n", style="#cc0000")
        info_text.append(f"   RAM:      ", style="#880000")
        info_text.append(f"{self.start_mem}\n", style="#cc0000")
        
        header_content = Columns([styled_ascii, info_text], expand=False)
        header_panel = Panel(
            header_content,
            box=box.HORIZONTALS,
            style="on #050000",
            border_style="#440000",
            padding=(1, 2)
        )
        console.print(header_panel)
        console.print(Text(f" 󱂵 {self.workspace}", style="dim #660000"), justify="center")
        console.print("")

    def handle_sigint(self, sig, frame):
        current_time = time.time()
        if current_time - self.last_ctrl_c < 2:
            console.print("\n[bold red]Exiting Rta...[/bold red]")
            sys.exit(0)
        else:
            self.last_ctrl_c = current_time
            console.print("\n[bold #ff4444]  (Press Ctrl+C again to exit)[/bold #ff4444]")

    def handle_slash_command(self, command_str):
        from rta_cli.commands import app
        parts = command_str[1:].split()
        if not parts: return
        cmd_name = parts[0].lower()
        args = parts[1:]

        if cmd_name == "help":
            console.print("\n[bold #ff3333]Available Commands:[/bold #ff3333]")
            console.print("  /clear         - Clear chat history & screen")
            console.print("  /cclear        - Clear conversation context only")
            console.print("  /load_history  - Load history from .rta/history.json")
            console.print("  /exit          - Exit the chat\n")
            return

        if cmd_name in ["clear", "cls"]:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.messages = []
            from rta_cli.context import clear_context
            clear_context(self.workspace)
            self.print_header()
            return

        if cmd_name == "cclear":
            self.messages = []
            from rta_cli.context import clear_context
            clear_context(self.workspace)
            console.print("[bold green]Conversation context cleared.[/bold green]")
            return

        if cmd_name == "load_history":
            self._load_history()
            console.print(f"[bold green]Loaded {len(self.messages)} messages from history.[/bold green]")
            return

        try:
            orig_argv = sys.argv
            sys.argv = ["rta", cmd_name] + args
            app()
            sys.argv = orig_argv
        except SystemExit: pass
        except Exception as e: console.print(f"[red]Error: {e}[/red]")

    def print_summary(self):
        duration = time.time() - self.session_usage["start_time"]
        mins, secs = divmod(int(duration), 60)
        
        cached = self.session_usage.get("cached", 0)
        total_in = self.session_usage.get("input", 0)
        saved_pct = (cached / total_in * 100) if total_in > 0 else 0
        
        summary = Text()
        summary.append("\n ──────────────── Session Summary ────────────────\n", style="dim #440000")
        summary.append(f"   Model:     {self.model}\n   Duration:  {mins}m {secs}s\n", style="#cc0000")
        summary.append(f"   Tokens:    In: {total_in} | Out: {self.session_usage['output']}\n", style="#cc0000")
        summary.append(f"   Caching:   {cached} tokens ({saved_pct:.1f}% saved)\n", style="#cc0000")
        summary.append(" ─────────────────────────────────────────────────\n", style="dim #440000")
        console.print(Panel(summary, border_style="#440000", box=box.ROUNDED, padding=(1, 2)))

    def get_prompt(self):
        return "\001\x1b[1;37;48;2;136;0;0m\002 rta \001\x1b[0m\002\001\x1b[1;38;2;255;51;51m\002 ❯ \001\x1b[0m\002 "

    def run(self, initial_prompt=None):
        signal.signal(signal.SIGINT, self.handle_sigint)
        os.system('cls' if os.name == 'nt' else 'clear')
        self._load_history()
        self.print_header()

        # Add system prompt if messages are empty or just started
        if not self.messages or not any(m.get("role") == "system" for m in self.messages):
            system_prompt = f"You are an expert developer CLI assistant. You are working in: {self.workspace}\n"
            system_prompt += f"Project Info: {json.dumps(self.project_info, indent=2)}\n"
            system_prompt += "Guidelines:\n"
            system_prompt += "- Use run_command for shell commands, not Python\n"
            system_prompt += "- Prefer glob + get_file_contents before editing\n"
            system_prompt += "- Always verify after edit (get_file_contents)\n"
            system_prompt += "- Explain errors in user-friendly terms\n"
            system_prompt += "- Ask before destructive operations (use your judgment)\n"
            self.messages.insert(0, {"role": "system", "content": system_prompt})
        
        while True:
            try:
                if initial_prompt:
                    user_input = initial_prompt
                    initial_prompt = None # Only use once
                else:
                    user_input = input(self.get_prompt()).strip()
                
                if not user_input: continue
                if user_input.startswith("/"):
                    cmd = user_input[1:].lower()
                    if cmd in ["exit", "quit"]: break
                    self.handle_slash_command(user_input)
                    continue

                think_mode = "think_it" in user_input
                if think_mode:
                    hl = "[bold #ff0000]t[/][bold #00ff00]h[/][bold #0000ff]i[/][bold #ffff00]n[/][bold #ff00ff]k[/][bold #00ffff]_[/][bold #ffffff]i[/][bold #ff8800]t[/]"
                    console.print(f" [dim]Prompt:[/dim] {user_input.replace('think_it', hl)}")

                from rta_cli.agent import run_agent
                from rta_cli.safety import set_active_status
                msg = random.choice(LOADING_MESSAGES)
                
                with console.status(f"[bold #ff3333]{msg}[/bold #ff3333]", spinner="dots") as status:
                    set_active_status(status)
                    res, usage, new_turn = run_agent(
                        user_input, 
                        self.workspace, 
                        self.messages, 
                        self.provider, 
                        self.model, 
                        think=think_mode,
                        session_id=self.session_id,
                        turn_index=self.turn_index,
                        timeout=self.timeout,
                        force=self.force,
                    )
                    self.turn_index = new_turn

                self._trim_messages()
                self._save_history()
                self.session_usage["input"] += usage.get("prompt_tokens", 0)
                self.session_usage["output"] += usage.get("candidate_tokens", 0)
                self.session_usage["total"] += usage.get("total_tokens", 0)
                self.session_usage["cached"] += usage.get("cached_tokens", 0)

                console.print(f"\n[bold #ff3333]Rta[/bold #ff3333]")
                console.print(Panel(Markdown(res), border_style="#440000", padding=(1, 2)))

                console.print(f"\n[dim #440000]─── {self.workspace_name} ───[/dim #440000]\n")
                
            except (EOFError, KeyboardInterrupt): break
            except Exception as e: console.print(f"[red]Error: {e}[/red]")
        
        self.print_summary()

def start_chat():
    RtaChat().run()
