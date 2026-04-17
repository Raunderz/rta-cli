import os
import sys
import time
import signal
import subprocess
import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.markdown import Markdown

console = Console()

ASCII_ART = """ _  .-')   .-') _      ('-.     
( \( -O ) (  OO) )    ( OO ).-. 
 ,------. /     '._   / . --. / 
 |   /`. '|'--...__)  | \-.  \  
 |  /  | |'--.  .--'.-'-'  |  | 
 |  |_.' |   |  |    \| |_.'  | 
 |  .  '.'   |  |     |  .-.  | 
 |  |\  \    |  |     |  | |  | 
 `--' '--'   `--'     `--' `--' """

class RtaChat:
    def __init__(self):
        self.last_ctrl_c = 0
        self.workspace = os.path.abspath(os.getcwd())
        self.workspace_name = os.path.basename(self.workspace)
        self.version = "v0.0.1"
        self.ascii_art = ASCII_ART
        self.user = "Guest"
        
        # Load model from config
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.model = "gemini-2.5-flash"
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.model = json.load(f).get("model", self.model)
                
        self.messages = []
        self.start_mem = self._get_memory_usage()

    def _get_memory_usage(self):
        try:
            if os.path.exists('/proc/self/status'):
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            return f"{int(line.split()[1]) / 1024:.1f} MB"
            if os.name == 'posix':
                import resource
                return f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.1f} MB"
            else:
                out = subprocess.check_output(['tasklist', '/FI', f'PID eq {os.getpid()}', '/FO', 'CSV', '/NH']).decode()
                return f"{int(out.split(',')[4].strip('\"').replace(' K', '').replace(',', '')) / 1024:.1f} MB"
        except:
            return "N/A"

    def print_header(self):
        ascii_lines = self.ascii_art.splitlines()
        styled_ascii = Text()
        for i, line in enumerate(ascii_lines):
            color = f"#{max(50, 200 - i*20):02x}0000"
            styled_ascii.append(line + "\n", style=f"bold {color}")
        
        info_text = Text()
        info_text.append(f"\n   Rta Cli {self.version}\n", style="bold #ff3333")
        info_text.append(f"   User:  ", style="#880000")
        info_text.append(f"{self.user}\n", style="#cc0000")
        info_text.append(f"   Model: ", style="#880000")
        info_text.append(f"{self.model}\n", style="#cc0000")
        info_text.append(f"   RAM:   ", style="#880000")
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
        import typer
        parts = command_str[1:].split()
        if not parts:
            return
        cmd_name = parts[0].lower()
        args = parts[1:]

        if cmd_name == "help":
            console.print("\n[bold #ff3333]Available Commands:[/bold #ff3333]")
            console.print("  /model <name> - Change the Gemini model")
            console.print("  /clear         - Clear chat history & screen")
            console.print("  /init          - Initialize a new project")
            console.print("  /auth          - Authenticate with Rta backend")
            console.print("  /clone         - Clone a repository")
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
            return

        if cmd_name in ["clear", "cls"]:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.messages = []
            self.print_header()
            return

        try:
            orig_argv = sys.argv
            sys.argv = ["rta", cmd_name] + args
            app()
            sys.argv = orig_argv
        except SystemExit:
            pass
        except Exception as e:
            console.print(f"[red]Error executing command: {e}[/red]")

    def run(self):
        signal.signal(signal.SIGINT, self.handle_sigint)
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_header()
        while True:
            try:
                prompt = Text(" rta ", style="bold black on #880000")
                prompt.append(" ❯ ", style="#880000")
                user_input = console.input(prompt).strip()
                if not user_input:
                    continue
                if user_input.startswith("/"):
                    cmd = user_input[1:].lower()
                    if cmd in ["exit", "quit"]:
                        break
                    self.handle_slash_command(user_input)
                    continue
                from rta_cli.agent import run_agent
                with console.status("[bold #ff3333]Agent is thinking...[/bold #ff3333]", spinner="dots"):
                    response_text = run_agent(user_input, self.workspace, self.messages)
                console.print(f"\n[bold #ff3333]Rta[/bold #ff3333]")
                console.print(Markdown(response_text))
                console.print(f"\n[dim #440000]─── {self.workspace_name} ───[/dim #440000]\n")
            except EOFError:
                break
            except KeyboardInterrupt:
                continue
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

def start_chat():
    chat = RtaChat()
    chat.run()
