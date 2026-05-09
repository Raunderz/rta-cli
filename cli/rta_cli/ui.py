import sys
import re

class Console:
    def print(self, *args, **kwargs):
        text = " ".join(map(str, args))
        text = self._colorize(text)
        file = kwargs.get("file", sys.stdout)
        print(text, file=file)

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
            parts = tag.split()
            codes = []
            for p in parts:
                if p in colors:
                    codes.append(colors[p])
                elif p.startswith("#"):
                    codes.append("1")
            
            if not codes:
                return match.group(0)
            return f"\033[{';'.join(codes)}m"

        text = re.sub(r"\[([a-z0-9 #]+)\]", replace_tag, text)
        text = text.replace("[/]", "\033[0m")
        if "\033[" in text and not text.endswith("\033[0m"):
            text += "\033[0m"
        return text

    def status(self, message, spinner="dots"):
        class StatusContext:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def start(self): pass
            def stop(self): pass
        return StatusContext()


def markdown(text):
    # Very basic Markdown to ANSI
    text = re.sub(r"^# (.*)$", r"\033[1;31m\1\033[0m", text, flags=re.M)
    text = re.sub(r"^## (.*)$", r"\033[1;32m\1\033[0m", text, flags=re.M)
    text = re.sub(r"^### (.*)$", r"\033[1;36m\1\033[0m", text, flags=re.M)
    text = re.sub(r"\*\*(.*?)\*\*", r"\033[1m\1\033[0m", text)
    text = re.sub(r"`(.*?)`", r"\033[33m\1\033[0m", text)
    text = re.sub(r"```(.*?)\n(.*?)```", r"\033[36m\2\033[0m", text, flags=re.S)
    return text


def panel(text, title=None, border_style=""):
    lines = str(text).splitlines()
    width = max(len(l) for l in lines) if lines else 0
    if title:
        width = max(width, len(title) + 4)
    
    output = []
    top = f"┌─ {title} " if title else "┌─"
    output.append(top + "─" * (width - len(top) + 2) + "┐")
    for l in lines:
        output.append(f"│ {l:<{width}} │")
    output.append("└" + "─" * (width + 2) + "┘")
    return "\n".join(output)


def table(title, columns, rows):
    output = [f"\n=== {title} ==="]
    header = " | ".join(columns)
    output.append(header)
    output.append("-" * len(header))
    for r in rows:
        output.append(" | ".join(map(str, r)))
    return "\n".join(output)

class Text(str):
    def append(self, text, style=None):
        # Dummy for rich compatibility
        return self + text
