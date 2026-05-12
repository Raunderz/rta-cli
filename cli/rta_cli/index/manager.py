import os
import json
import math
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any

from rta_cli.utils import _rta_dir

class BM25Indexer:
    """Pure Python BM25 Indexer for Lean RAG."""
    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        self.project_id = hashlib.md5(self.workspace_path.encode()).hexdigest()
        self.storage_dir = os.path.join(_rta_dir(), "index", self.project_id)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.index_file = os.path.join(self.storage_dir, "bm25_index.json")
        
        self.k1 = 1.5
        self.b = 0.75
        
        self.corpus = [] # List of {text, file_path, start_line, end_line, file_hash}
        self.df = {}     # Document frequency for each term
        self.avgdl = 0   # Average document length
        self.doc_count = 0
        
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r") as f:
                    data = json.load(f)
                    self.corpus = data.get("corpus", [])
                    self.df = data.get("df", {})
                    self.avgdl = data.get("avgdl", 0)
                    self.doc_count = len(self.corpus)
            except Exception:
                pass

    def _save_index(self):
        with open(self.index_file, "w") as f:
            json.dump({
                "corpus": self.corpus,
                "df": self.df,
                "avgdl": self.avgdl
            }, f)

    def _tokenize(self, text: str) -> List[str]:
        # Simple word tokenization, removing symbols
        return re.findall(r'\w+', text.lower())

    def chunk_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        lines = content.splitlines()
        chunks = []
        chunk_size = 50
        overlap = 10
        
        for i in range(0, len(lines), chunk_size - overlap):
            chunk_lines = lines[i : i + chunk_size]
            if not chunk_lines: break
            
            text = "\n".join(chunk_lines)
            chunks.append({
                "text": text,
                "tokens": self._tokenize(text),
                "file_path": file_path,
                "start_line": i + 1,
                "end_line": i + len(chunk_lines),
            })
            if i + chunk_size >= len(lines): break
        return chunks

    def index_project(self, force: bool = False):
        indexed_files = {c["file_path"]: c["file_hash"] for c in self.corpus}
        new_corpus = []
        changed = False

        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "dist" and d != "build"]
            for file in files:
                if file.startswith(".") or file.endswith((".pyc", ".png", ".jpg", ".zip", ".bin", ".exe")):
                    continue
                
                rel_path = os.path.relpath(os.path.join(root, file), self.workspace_path)
                abs_path = os.path.join(root, file)
                
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    file_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    if not force and indexed_files.get(rel_path) == file_hash:
                        # Keep existing chunks for this file
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
            # Clean up tokens from corpus to save space before saving
            save_corpus = []
            for c in self.corpus:
                copy = c.copy()
                if "tokens" in copy: del copy["tokens"]
                save_corpus.append(copy)
            
            # Save actual state
            self._save_index()

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query)
        scores = []

        for doc_idx, doc in enumerate(self.corpus):
            score = 0
            doc_tokens = self._tokenize(doc["text"]) # Re-tokenize for scoring to keep memory low
            doc_len = len(doc_tokens)
            
            # Count term frequencies in doc
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
