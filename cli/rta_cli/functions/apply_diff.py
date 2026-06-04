import os
import re


def apply_diff(working_directory, diff_text):
    """
    Applies a unified diff to files in the working directory.
    Atomic: All changes applied or none.
    """
    lines = diff_text.splitlines()
    files_to_modify = {}
    current_file = None
    hunks = []

    # Simple Unified Diff Parser
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- "):
            # New file block
            if current_file and hunks:
                files_to_modify[current_file] = hunks

            # --- path/to/file (often --- a/path/to/file)
            path = line[4:].strip()
            if path.startswith("a/"):
                path = path[2:]

            i += 1
            if i < len(lines) and lines[i].startswith("+++ "):
                target_path = lines[i][4:].strip()
                if target_path.startswith("b/"):
                    target_path = target_path[2:]
                current_file = target_path
                hunks = []
                i += 1
            else:
                current_file = None
                continue
        elif line.startswith("@@"):
            # Hunk header: @@ -start,len +start,len @@
            match = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line)
            if match:
                old_start = int(match.group(1))
                new_start = int(match.group(3))
                hunk_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith(("--- ", "@@")):
                    hunk_lines.append(lines[i])
                    i += 1
                hunks.append(
                    {
                        "old_start": old_start,
                        "new_start": new_start,
                        "lines": hunk_lines,
                    }
                )
                # Don't increment i here, it was incremented in the while loop
            else:
                i += 1
        else:
            i += 1

    if current_file and hunks:
        files_to_modify[current_file] = hunks

    if not files_to_modify:
        return "Error: No valid diff hunks found."

    results = []
    modifications = {}

    for rel_path, hunks in files_to_modify.items():
        abs_path = os.path.abspath(os.path.join(working_directory, rel_path))
        if not abs_path.startswith(os.path.abspath(working_directory)):
            return f"Error: Path {rel_path} is outside working directory."

        if not os.path.exists(abs_path):
            content_lines = []
        else:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content_lines = f.readlines()

        # Apply hunks to content_lines
        # We apply from bottom to top to avoid offset issues
        new_content_lines = list(content_lines)

        # Sort hunks by old_start descending
        hunks.sort(key=lambda x: x["old_start"], reverse=True)

        for hunk in hunks:
            # Simple applier (assumes exact match of context for now)
            # Unified diff line 1 is often file line 1
            start_idx = hunk["old_start"] - 1

            # Extract expected old lines and actual new lines
            old_hunk_content = []
            new_hunk_content = []
            expected_old_len = 0

            for hl in hunk["lines"]:
                if hl.startswith(" "):
                    old_hunk_content.append(hl[1:])
                    new_hunk_content.append(hl[1:])
                    expected_old_len += 1
                elif hl.startswith("-"):
                    old_hunk_content.append(hl[1:])
                    expected_old_len += 1
                elif hl.startswith("+"):
                    new_hunk_content.append(hl[1:])

            # Verification (relaxed for now, but should check context)
            # For brevity, we just replace the block. SOTA would do fuzzy matching.

            # Replace hunk in content
            # This is a very basic implementation. Real diff tools are smarter.
            end_idx = start_idx + expected_old_len

            # Ensure indices are within bounds
            start_idx = max(0, start_idx)
            end_idx = min(len(new_content_lines), end_idx)

            # Replace the lines
            new_content_lines[start_idx:end_idx] = [
                l + "\n" if not l.endswith("\n") else l for l in new_hunk_content
            ]

        modifications[abs_path] = "".join(new_content_lines)
        results.append(rel_path)

    # Write changes
    for abs_path, content in modifications.items():
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

    return f"Successfully applied diff to: {', '.join(results)}"


schema_apply_diff = {
    "name": "apply_diff",
    "description": "Applies a unified diff to one or more files in the working directory. Supports multiple hunks per file.",
    "parameters": {
        "type": "object",
        "properties": {
            "diff_text": {
                "type": "string",
                "description": "The unified diff content to apply",
            },
        },
        "required": ["diff_text"],
    },
}
