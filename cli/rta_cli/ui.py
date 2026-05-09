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
            if not codes:
                return match.group(0)
            return f"\033[{';'.join(codes)}m"

        text = re.sub(r"\[([a-z0-9 ]+)\]", replace_tag, text)
        text = text.replace("[/]", "\033[0m")
        return text

    def status(self, message, spinner="dots"):
        class StatusContext:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def start(self): pass
            def stop(self): pass
        return StatusContext()

def markdown(text):
    # Just basic bold and code highlighting, no headers or blocks
    text = re.sub(r"\*\*(.*?)\*\*", r"\033[1m\1\033[0m", text)
    text = re.sub(r"`(.*?)`", r"\033[33m\1\033[0m", text)
    return text

class Text(str):
    def append(self, text, style=None): return self + text
