import hashlib
import json
import math
import os
import re
from typing import Any


def _rta_dir() -> str:
    import platform

    if platform.system() == "Windows":
        base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, ".rta")


class BM25Indexer:
    """Pure Python BM25 Indexer for Lean RAG."""

    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        self.project_id = hashlib.md5(self.workspace_path.encode()).hexdigest()
        self.storage_dir = os.path.join(_rta_dir(), "index", self.project_id)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.index_file = os.path.join(self.storage_dir, "bm25_index.json")
        self.skeleton_file = os.path.join(self.storage_dir, "skeleton.md")

        self.k1 = 1.5
        self.b = 0.75

        self.corpus = []  # List of {text, file_path, start_line, end_line, file_hash}
        self.df = {}  # Document frequency for each term
        self.avgdl = 0  # Average document length
        self.doc_count = 0

        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file) as f:
                    data = json.load(f)
                    self.corpus = data.get("corpus", [])
                    self.df = data.get("df", {})
                    self.avgdl = data.get("avgdl", 0)
                    self.doc_count = len(self.corpus)
            except Exception:
                pass

    def _save_index(self):
        with open(self.index_file, "w") as f:
            json.dump({"corpus": self.corpus, "df": self.df, "avgdl": self.avgdl}, f)

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    def chunk_file(self, file_path: str, content: str) -> list[dict[str, Any]]:
        lines = content.splitlines()
        chunks = []
        chunk_size = 50
        overlap = 10

        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i : i + chunk_size]
            if not chunk_lines:
                break

            text = "\n".join(chunk_lines)
            chunks.append(
                {
                    "text": text,
                    "tokens": self._tokenize(text),
                    "file_path": file_path,
                    "start_line": i + 1,
                    "end_line": i + len(chunk_lines),
                }
            )
            if i + chunk_size >= len(lines):
                break
        return chunks

    def index_project(self, force: bool = False):
        indexed_files = {c["file_path"]: c["file_hash"] for c in self.corpus}
        new_corpus = []
        changed = False

        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ("node_modules", "dist", "build", "venv", ".venv")
            ]
            for file in files:
                if file.startswith(".") or file.endswith(
                    (".pyc", ".png", ".jpg", ".zip", ".bin", ".exe", ".lock")
                ):
                    continue

                rel_path = os.path.relpath(os.path.join(root, file), self.workspace_path)
                abs_path = os.path.join(root, file)

                try:
                    with open(abs_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    file_hash = hashlib.md5(content.encode()).hexdigest()

                    if not force and indexed_files.get(rel_path) == file_hash:
                        new_corpus.extend([c for c in self.corpus if c["file_path"] == rel_path])
                        continue

                    changed = True
                    chunks = self.chunk_file(rel_path, content)
                    for chunk in chunks:
                        chunk["file_hash"] = file_hash
                        new_corpus.append(chunk)
                except Exception:
                    continue

        if changed or not self.corpus:
            self.corpus = new_corpus
            self.doc_count = len(self.corpus)
            self.df = {}
            total_len = 0

            for doc in self.corpus:
                tokens = doc.get("tokens", [])
                total_len += len(tokens)
                unique_tokens = set(tokens)
                for token in unique_tokens:
                    self.df[token] = self.df.get(token, 0) + 1

            self.avgdl = total_len / self.doc_count if self.doc_count > 0 else 0

            # Save actual state (clean up tokens before saving to disk)
            save_corpus = []
            for c in self.corpus:
                copy = c.copy()
                if "tokens" in copy:
                    del copy["tokens"]
                save_corpus.append(copy)

            with open(self.index_file, "w") as f:
                json.dump({"corpus": save_corpus, "df": self.df, "avgdl": self.avgdl}, f)

            self._generate_skeleton()

    def _generate_skeleton(self):
        skeleton = ["# Project Skeleton\n"]

        # Group by file
        files_to_chunks = {}
        for doc in self.corpus:
            path = doc["file_path"]
            if path not in files_to_chunks:
                files_to_chunks[path] = []
            files_to_chunks[path].append(doc)

        for file_path, chunks in files_to_chunks.items():
            if not file_path.endswith(
                (
                    ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".go",
                    ".rs",
                    ".cs",
                    ".c",
                    ".cpp",
                    ".h",
                    ".hpp",
                )
            ):
                continue

            skeleton.append(f"## {file_path}")

            patterns = [
                r"^\s*(class\s+\w+)",
                r"^\s*(def\s+\w+\s*\(.*?\))",
                r"^\s*(function\s+\w+\s*\(.*?\))",
                r"^\s*(async\s+function\s+\w+)",
                r"^\s*(async\s+def\s+\w+)",
                r"^\s*(fn\s+\w+\s*\(.*?\))",
                r"^\s*(pub\s+fn\s+\w+\s*\(.*?\))",
                r"^\s*(struct\s+\w+)",
            ]

            file_sigs = set()
            for doc in chunks:
                for line in doc["text"].splitlines():
                    for p in patterns:
                        match = re.search(p, line)
                        if match:
                            sig = match.group(1).strip()
                            file_sigs.add(f"- `{sig}`")

            skeleton.extend(sorted(list(file_sigs)))

        with open(self.skeleton_file, "w") as f:
            f.write("\n".join(skeleton))

    def get_skeleton(self) -> str:
        if os.path.exists(self.skeleton_file):
            with open(self.skeleton_file) as f:
                return f.read()
        return "Skeleton not generated yet. Indexing might be needed."

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_tokens = self._tokenize(query)
        scores = []

        for doc in self.corpus:
            score = 0
            doc_tokens = self._tokenize(doc["text"])
            doc_len = len(doc_tokens)
            tf_map = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            for token in query_tokens:
                if token not in self.df:
                    continue
                df_t = self.df[token]
                idf = math.log((self.doc_count - df_t + 0.5) / (df_t + 0.5) + 1.0)
                tf = tf_map.get(token, 0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                score += idf * (numerator / denominator)

            if score > 0:
                scores.append((score, doc))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scores[:limit]]
