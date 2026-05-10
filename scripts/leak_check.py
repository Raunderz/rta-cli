import os
import re
import sys

# Patterns to search for
PATTERNS = {
    "OpenAI": r"sk-[a-zA-Z0-9]{32,}",
    "Groq": r"gsk_[a-zA-Z0-9]{32,}",
    "Google/Gemini": r"AIza[0-9A-Za-z_-]{35}",
    "Rta Key": r"rta_[a-zA-Z0-9_-]{32,}",
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Generic Secret": r'(?i)(password|secret|key|token|auth)["\s:]+[\'"]?[A-Za-z0-9\-\._~\+\/]{16,}[\'"]?',
}

# Directories to ignore
IGNORE_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", ".rta", ".browser_modules", "lib", "src-gen"}
# Files to ignore
IGNORE_FILES = {".env.example", "package-lock.json", "bun.lock", "leak_check.py",".env"}

def scan_file(filepath):
    if filepath.endswith(".map") or filepath.endswith(".png") or filepath.endswith(".jpg"):
        return []
    leaks = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for name, pattern in PATTERNS.items():
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Basic heuristic to avoid some false positives
                    val = match.group(0)
                    if "integrity" in content.lower() and "sha" in val.lower():
                        continue
                    
                    line_no = content.count('\n', 0, match.start()) + 1
                    leaks.append((name, line_no, val))
    except Exception as e:
        pass
    return leaks

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"--- Scanning {root_dir} for leaks ---")
    
    total_leaks = 0
    for root, dirs, files in os.walk(root_dir):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
                
            filepath = os.path.join(root, file)
            leaks = scan_file(filepath)
            if leaks:
                rel_path = os.path.relpath(filepath, root_dir)
                print(f"\n[!] Potential leaks in {rel_path}:")
                for name, line, val in leaks:
                    # Mask most of the key for safety in output
                    masked = val[:6] + "..." + val[-4:] if len(val) > 10 else "..."
                    print(f"    - L{line}: {name} found ({masked})")
                total_leaks += len(leaks)

    if total_leaks == 0:
        print("\n[+] No leaks found.")
    else:
        print(f"\n[!] Total potential leaks: {total_leaks}")
        sys.exit(1)

if __name__ == "__main__":
    main()
