import os
import sys
import time
import signal
import subprocess
import json
import random
try:
    import readline
except ImportError:
    pass # Windows might not have it by default

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
    "Thinking in TOON..."
]

class RtaChat:
    def __init__(self):
        self.last_ctrl_c = 0
        self.workspace = os.path.abspath(os.getcwd())
        self.workspace_name = os.path.basename(self.workspace)
        self.version = "v0.0.2"
        self.ascii_art = ASCII_ART
        self.user = "Guest"
        
        if hasattr(sys, '_MEIPASS'):
            self.config_path = os.path.join(sys._MEIPASS, 'rta_cli', 'config.json')
        else:
            self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            
        self.model = "nvidia/nemotron-3-super-120b-a12b:free"
        self.provider = "openrouter"
        
        if not os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'w') as f:
                    json.dump({
                        "model": self.model,
                        "provider": self.provider,
                        "server_url": "http://localhost:8000"
                    }, f, indent=4)
            except:
                pass
        else:
            with open(self.config_path, 'r') as f:
                cfg = json.load(f)
                self.model = cfg.get("model", self.model)
                self.provider = cfg.get("provider", self.provider)

        self.messages = []
        self.rta_dir = os.path.join(self.workspace, ".rta")
        self.history_path = os.path.join(self.rta_dir, "history.json")
        self._load_history()

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
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, 'r') as f:
                    self.messages = json.load(f)
            except:
                self.messages = []

    def _save_history(self):
        if not os.path.exists(self.rta_dir):
            os.makedirs(self.rta_dir, exist_ok=True)
        try:
            with open(self.history_path, 'w') as f:
                json.dump(self.messages, f, indent=2)
        except:
            pass

    def _trim_messages(self, max_msgs=8):
        if len(self.messages) > max_msgs:
            self.messages = self.messages[:2] + self.messages[-(max_msgs-2):]
        
        # Aggressively prune older tool results to save tokens and reduce 'context noise'
        # We prune everything except the last 2 turns.
        for msg in self.messages[:-2]:
            if msg.get("role") == "function":
                for part in msg.get("parts", []):
                    if "functionResponse" in part:
                        fr = part["functionResponse"]
                        resp = fr.get("response", {})
                        content = resp.get("content", "")
                        if isinstance(content, str) and len(content) > 150:
                            resp["content"] = content[:150] + "\n[... HISTORICAL TOOL RESULT TRUNCATED ...]"

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
            console.print("  /model <name> - Change the model")
            console.print("  /provider <name> - Switch between google/ollama/cloudflare")
            console.print("  /clear         - Clear chat history & screen")
            console.print("  /cclear        - Clear conversation context only")
            console.print("  /exit          - Exit the chat\n")
            return

        if cmd_name == "model":
            if not args:
                console.print(f"[bold #ff3333]Current model: [/bold #ff3333]{self.model}")
                return
            new_model = args[0]
            self.model = new_model
            with open(self.config_path, 'r+') as f:
                config = json.load(f)
                config['model'] = new_model
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()
            console.print(f"[bold green]Model updated to: {new_model}[/bold green]")
            self.print_header()
            return

        if cmd_name in ["provider", "providers"]:
            if not args:
                console.print(f"[bold #ff3333]Current provider: [/bold #ff3333]{self.provider}")
                return
            new_prov = args[0].lower()
            if new_prov not in ["google", "ollama", "cloudflare", "openrouter"]:
                console.print(f"[bold red]Unsupported provider: {new_prov}[/bold red]")
                return
            self.provider = new_prov
            
            # Set default models for specific providers
            if new_prov == "cloudflare":
                self.model = "llama-3-8b-instruct"
            elif new_prov == "openrouter":
                self.model = "nvidia/nemotron-3-super-120b-a12b:free"
            
            with open(self.config_path, 'r+') as f:
                config = json.load(f)
                config['provider'] = new_prov
                config['model'] = self.model
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()
            console.print(f"[bold green]Provider updated to: {new_prov}[/bold green]")
            self.print_header()
            return

        if cmd_name in ["clear", "cls"]:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.messages = []
            if os.path.exists(self.history_path): os.remove(self.history_path)
            self._save_history()
            self.print_header()
            return

        if cmd_name == "cclear":
            self.messages = []
            if os.path.exists(self.history_path): os.remove(self.history_path)
            self._save_history()
            console.print("[bold green]Conversation context cleared.[/bold green]")
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

    def run(self):
        signal.signal(signal.SIGINT, self.handle_sigint)
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_header()
        
        while True:
            try:
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
                msg = random.choice(LOADING_MESSAGES)
                
                with console.status(f"[bold #ff3333]{msg}[/bold #ff3333]", spinner="dots"):
                    res, usage = run_agent(user_input, self.workspace, self.messages, self.provider, self.model, think=think_mode)

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
