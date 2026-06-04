import sys
import re


class Console:
    def print(self, *args, **kwargs):
        text = " ".join(map(str, args))
        text = self._colorize(text)
        file = kwargs.get("file", sys.stdout)
        end = kwargs.get("end", "\n")
        print(text, file=file, end=end, flush=True)

    def input(self, prompt=""):
        prompt = self._colorize(prompt)
        return input(prompt)

    def _colorize(self, text):
        colors = {
            "red": "31",
            "green": "32",
            "yellow": "33",
            "blue": "34",
            "magenta": "35",
            "cyan": "36",
            "white": "37",
            "dim": "2",
            "bold": "1",
        }

        def replace_tag(match):
            tag = match.group(1)
            if tag.startswith("/"):
                return "\033[0m"

            parts = tag.split()
            codes = []
            for p in parts:
                if p in colors:
                    codes.append(colors[p])
            if not codes:
                return match.group(0)
            return f"\033[{';'.join(codes)}m"

        text = re.sub(r"\[([/a-z0-9 #]+)\]", replace_tag, text)
        return text

    def status(self, message, spinner="dots"):
        import threading
        import time

        class StatusContext:
            def __init__(self, console, message):
                self.console = console
                self.message = message
                self.running = False
                self.thread = None
                self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                if spinner == "pacman":
                    self.frames = ["ᗧ···", "ᗧ··", "ᗧ·", "ᗧ", " ᗧ", "  ᗧ"]

            def _spin(self):
                idx = 0
                while self.running:
                    frame = self.frames[idx % len(self.frames)]
                    # Use \r to return to start of line, then print frame + message
                    line = f"\r[bold cyan]{frame}[/bold cyan] [dim]{self.message}[/dim]"
                    sys.stdout.write("\033[K" + self.console._colorize(line))
                    sys.stdout.flush()
                    idx += 1
                    time.sleep(0.1)

            def __enter__(self):
                self.start()
                return self

            def __exit__(self, *args):
                self.stop()

            def start(self):
                if not self.running:
                    self.running = True
                    self.thread = threading.Thread(target=self._spin)
                    self.thread.daemon = True
                    self.thread.start()

            def stop(self):
                if self.running:
                    self.running = False
                    if self.thread:
                        self.thread.join(timeout=0.2)
                    sys.stdout.write("\r\033[K")
                    sys.stdout.flush()

            def update(self, message):
                self.message = message

        return StatusContext(self, message)


def markdown(text):
    # Very basic Markdown to ANSI
    text = re.sub(r"\*\*(.*?)\*\*", r"\033[1m\1\033[0m", text)
    text = re.sub(r"`(.*?)`", r"\033[33m\1\033[0m", text)
    # Code blocks
    text = re.sub(r"```[a-z]*\n?(.*?)```", r"\033[36m\1\033[0m", text, flags=re.S)
    return text


class Text(str):
    def append(self, text, style=None):
        return self + text
