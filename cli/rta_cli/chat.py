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

from rta_cli.ui import Console, markdown, Text
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
    "Reticulating splines...",
    "Consulting the digital oracle...",
    "Synthesizing silicon wisdom..."
]

class RtaChat:
    def __init__(self, workspace=None, session_id=None, timeout=300, force=False):
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
        self.version = "v0.3.0"
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
        print(self.ascii_art)
        console.print(f"\nRta Cli {self.version} | {self.user} | {self.workspace}\n")

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
        total_in = self.session_usage.get("input", 0)
        total_out = self.session_usage.get("output", 0)
        
        console.print(f"\n[dim]─ Session: {mins}m {secs}s | In: {total_in} | Out: {total_out} ─[/]\n")

    def get_prompt(self):
        return ">> "

    def run(self, initial_prompt=None):
        signal.signal(signal.SIGINT, self.handle_sigint)
        os.system('cls' if os.name == 'nt' else 'clear')
        self._load_history()
        self.print_header()

        # Add system prompt if messages are empty or just started
        if not self.messages or not any(m.get("role") == "system" for m in self.messages):
            system_prompt = f"You are Rta, an expert developer CLI assistant. Working in: {self.workspace}\n"
            system_prompt += f"Project: {json.dumps(self.project_info)}\n"
            system_prompt += "Rules:\n"
            system_prompt += "- Run shell commands via run_command tool, not Python\n"
            system_prompt += "- Read files with glob + get_file_contents before editing\n"
            system_prompt += "- Verify edits by reading the file back\n"
            system_prompt += "- Use parallel tool execution for independent reads\n"
            system_prompt += "- Ask before destructive ops (deletes, force-push, mass rewrites)\n"
            system_prompt += "- Responses stream in real-time — lead with the answer, then details\n"
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

                from rta_cli.agent import stream_agent
                
                full_text = ""
                usage = {}
                new_turn = self.turn_index
                printed_header = False

                # Start spinner
                status = console.status(random.choice(LOADING_MESSAGES), spinner="pacman")
                status.start()

                try:
                    gen = stream_agent(
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
                    
                    for event in gen:
                        if event["type"] == "provider":
                            creative_msgs = [
                                "Tuning the neural arrays...",
                                "Consulting the digital oracle...",
                                "Synthesizing logic gates...",
                                "Reticulating splines...",
                                "Optimizing thought vectors...",
                                "Gathering silicon wisdom...",
                                "Architecting a solution...",
                                "Traversing the latent space..."
                            ]
                            status.update(random.choice(creative_msgs))
                            continue
                        elif event["type"] == "thought":
                            # If we see a thought, maybe stop spinner and show it?
                            # For now, just update status message
                            status.update(f"Thinking: {event['content'][:50]}...")
                            continue
                        
                        # Once we get text or tool, stop the spinner
                        if event["type"] in ["text_chunk", "text", "tool_start"]:
                            status.stop()

                        if event["type"] == "text_chunk":
                            if not printed_header:
                                console.print(f"\n[bold red]Rta[/bold red]")
                                printed_header = True
                            console.print(event["content"], end="")
                            full_text += event["content"]
                        elif event["type"] == "text":
                            if not printed_header:
                                console.print(f"\n[bold red]Rta[/bold red]")
                                printed_header = True
                            full_text += event["content"]
                        elif event["type"] == "tool_start":
                            if not printed_header:
                                console.print(f"\n[bold red]Rta[/bold red]")
                                printed_header = True
                            
                            name = event["content"]
                            args = event.get("arguments", "{}")
                            try:
                                args_obj = json.loads(args)
                                args_str = json.dumps(args_obj, indent=2)
                                if len(args) < 60:
                                    args_str = json.dumps(args_obj)
                            except:
                                args_str = args
                            
                            console.print(f"\n\n[bold cyan]🔨 Executing tool:[/bold cyan] [green]{name}[/green]")
                            if args_str and args_str != "{}":
                                console.print(f"[dim]{args_str}[/dim]\n")
                        elif event["type"] == "usage":
                            usage = event["content"]
                            new_turn = event.get("turn_index", new_turn)
                        elif event["type"] == "error":
                            status.stop()
                            console.print(f"\n[red]Error: {event['content']}[/red]")
                finally:
                    status.stop()

                self.turn_index = new_turn

                self._trim_messages()
                self._save_history()
                self.session_usage["input"] += usage.get("prompt_tokens", 0)
                self.session_usage["output"] += usage.get("candidate_tokens", 0)
                self.session_usage["total"] += usage.get("total_tokens", 0)
                self.session_usage["cached"] += usage.get("cached_tokens", 0)

                console.print(f"\n[dim]─── {self.workspace_name} ───[/dim]\n")
                
            except (EOFError, KeyboardInterrupt): break
            except Exception as e: console.print(f"[red]Error: {e}[/red]")
        
        self.print_summary()

def start_chat():
    RtaChat().run()
