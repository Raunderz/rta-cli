r"""
Credential storage, device fingerprint, and server URL helpers.

Single source of truth for:
  - ~/.rta/  (Linux/Mac)  or  %USERPROFILE%\.rta\  (Windows)
  - API key storage (base64 obfuscated, 0o600 perms on Unix)
  - Device fingerprint (UUID, persisted across runs)
  - Server URL (edit SERVER_URL below to change for dev/staging/prod)
"""
import os
import sys
import uuid
import base64
import platform

# ──────────────────────────────────────────────────────────────────────────────
# SERVER URL — single point of truth. Change this for dev/staging.
# Can also be overridden by ~/.rta/config.json  {"server_url": "..."}
# ──────────────────────────────────────────────────────────────────────────────
SERVER_URL = "https://rta-tb0k.onrender.com"


def get_server_url() -> str:
    """
    Return the backend server URL.
    Priority: ~/.rta/config.json > bundled config.json > SERVER_URL constant.
    """
    # 1. User override in ~/.rta/config.json
    user_cfg = os.path.join(_rta_dir(), "config.json")
    if os.path.exists(user_cfg):
        try:
            import json
            with open(user_cfg) as f:
                url = json.load(f).get("server_url")
            if url:
                return url.rstrip("/")
        except Exception:
            pass

    # 2. Bundled config.json (project / PyInstaller bundle)
    try:
        if hasattr(sys, "_MEIPASS"):
            cfg_path = os.path.join(sys._MEIPASS, "rta_cli", "config.json")
        else:
            cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(cfg_path):
            import json
            with open(cfg_path) as f:
                url = json.load(f).get("server_url")
            if url:
                return url.rstrip("/")
    except Exception:
        pass

    # 3. Fallback constant
    return SERVER_URL


# ──────────────────────────────────────────────────────────────────────────────
# Directory helpers — cross-platform
# ──────────────────────────────────────────────────────────────────────────────

def _rta_dir() -> str:
    """
    Return the Rta credentials directory.
    - Linux / Mac:  ~/.rta/
    - Windows:      %USERPROFILE%\\.rta\\
    """
    if platform.system() == "Windows":
        base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, ".rta")


def _credentials_file() -> str:
    return os.path.join(_rta_dir(), "credentials")


def _device_id_file() -> str:
    return os.path.join(_rta_dir(), ".device_id")


def _ensure_rta_dir() -> None:
    """Create the .rta directory with tight permissions."""
    d = _rta_dir()
    os.makedirs(d, exist_ok=True)
    if platform.system() != "Windows":
        try:
            os.chmod(d, 0o700)
        except OSError:
            pass
    else:
        # Windows: set hidden attribute on the directory
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(d, 0x02)  # FILE_ATTRIBUTE_HIDDEN
        except Exception:
            pass


def _set_file_perms(path: str) -> None:
    """Tighten file permissions on Unix; no-op on Windows (NTFS ACLs handle it)."""
    if platform.system() != "Windows":
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Obfuscation (NOT encryption — prevents casual copy-paste leaking only)
# ──────────────────────────────────────────────────────────────────────────────

def _encode(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


def _decode(value: str) -> str:
    try:
        return base64.b64decode(value.encode()).decode()
    except Exception:
        return value  # legacy / plain-text fallback


# ──────────────────────────────────────────────────────────────────────────────
# Credential store
# ──────────────────────────────────────────────────────────────────────────────

def save_credential(key_name: str, value: str) -> None:
    """Write key_name=<obfuscated value> to the credentials file."""
    _ensure_rta_dir()
    creds = _credentials_file()

    entries: dict[str, str] = {}
    if os.path.exists(creds):
        with open(creds, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    entries[k.strip()] = v.strip()

    entries[key_name] = _encode(value)

    with open(creds, "w", encoding="utf-8") as f:
        for k, v in entries.items():
            f.write(f"{k}={v}\n")

    _set_file_perms(creds)


def load_credential(key_name: str) -> str | None:
    """Return decoded value for key_name, or None if absent."""
    creds = _credentials_file()
    if not os.path.exists(creds):
        return None
    with open(creds, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key_name:
                    return _decode(v.strip())
    return None


def delete_credential(key_name: str) -> None:
    """Remove a specific key from the credentials file."""
    creds = _credentials_file()
    if not os.path.exists(creds):
        return
    entries: dict[str, str] = {}
    with open(creds, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() != key_name:
                    entries[k.strip()] = v.strip()
    with open(creds, "w", encoding="utf-8") as f:
        for k, v in entries.items():
            f.write(f"{k}={v}\n")
    _set_file_perms(creds)


# ──────────────────────────────────────────────────────────────────────────────
# Device fingerprint
# ──────────────────────────────────────────────────────────────────────────────

def get_device_id() -> str:
    """Return a stable random UUID for this machine. Created on first call."""
    _ensure_rta_dir()
    did_file = _device_id_file()

    if os.path.exists(did_file):
        with open(did_file, "r", encoding="utf-8") as f:
            did = f.read().strip()
        if did:
            return did

    did = str(uuid.uuid4())
    with open(did_file, "w", encoding="utf-8") as f:
        f.write(did)
    _set_file_perms(did_file)
    return did
