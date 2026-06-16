import re
import json
import logging
import time
from collections import OrderedDict


class TTLCache:
    """Bounded dict with per-entry TTL and LRU eviction."""
    
    def __init__(self, max_size: int = 1000):
        self._max_size = max_size
        self._data: OrderedDict[str, tuple] = OrderedDict()
    
    def get(self, key: str):
        """Return value if present and not expired, else None. Moves key to end (most recent)."""
        if key not in self._data:
            return None
        value, expiry = self._data[key]
        if time.time() >= expiry:
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return value
    
    def set(self, key: str, value, ttl: float):
        """Store value with TTL. Evicts oldest entry if at capacity."""
        if key in self._data:
            del self._data[key]
        elif len(self._data) >= self._max_size:
            self._data.popitem(last=False)
        self._data[key] = (value, time.time() + ttl)
    
    def delete(self, key: str):
        self._data.pop(key, None)
    
    def __len__(self):
        return len(self._data)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        # Add request_id if available (from middleware)
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)

class Sanitizer:
    """Handles scrubbing of sensitive info before DB insertion."""

    @staticmethod
    def strip_secrets(text: str) -> str:
        """
        Scrubs sensitive information from the given text.
        Includes patterns for major AI providers and generic high-entropy strings.
        """
        if not text:
            return ""
            
        patterns = {
            "AWS": r'AKIA[0-9A-Z]{16}',
            "GCP": r'AIza[0-9A-Za-z_-]{35}',
            "OpenAI": r'sk-[a-zA-Z0-9]{48}',
            "Anthropic": r'sk-ant-api03-[a-zA-Z0-9\-_]{93}',
            "Stripe": r'sk_live_[0-9a-zA-Z]{24}',
            "Generic_Secret": r'(?i)(password|secret|key|token|auth|credential|api_key|private_key)["\s:]+([A-Za-z0-9\-\._~\+\/]{20,})',
        }

        for label, pattern in patterns.items():
            if label == "Generic_Secret":
                # For generic secrets, we preserve the label but scrub the value
                text = re.sub(pattern, r'\1: [SCRUBBED]', text)
            else:
                text = re.sub(pattern, f'[SCRUBBED_{label}]', text)

        # Path scrubbing: only absolute paths that look like they belong to a user's home.
        home_path_pattern = r'/home/[a-zA-Z0-9_-]+'
        text = re.sub(home_path_pattern, '/home/[USER]', text)

        return text

    @staticmethod
    def strip_paths(text: str) -> str:
        """
        Strips absolute paths in the text and replaces them with just the filename.
        """
        if not text:
            return ""
        path_pattern = r'/([a-zA-Z0-9_\-/]+)+'  
        return re.sub(path_pattern, lambda m: m.group(0).split('/')[-1], text)
