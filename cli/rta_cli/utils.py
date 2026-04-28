"""Credential storage and device fingerprint helpers."""
import os
import uuid
import stat
import base64

RTA_DIR = os.path.join(os.path.expanduser("~"), ".rta")
CREDENTIALS_FILE = os.path.join(RTA_DIR, "credentials")
DEVICE_ID_FILE = os.path.join(RTA_DIR, ".device_id")


def _ensure_rta_dir():
    """Create ~/.rta/ with 0o700 perms if missing."""
    if not os.path.exists(RTA_DIR):
        os.makedirs(RTA_DIR, mode=0o700, exist_ok=True)
    else:
        try:
            os.chmod(RTA_DIR, 0o700)
        except OSError:
            pass


def _encode(value: str) -> str:
    """Obfuscate value (not encryption — just casual copy-paste prevention)."""
    return base64.b64encode(value.encode()).decode()


def _decode(value: str) -> str:
    try:
        return base64.b64decode(value.encode()).decode()
    except Exception:
        return value  # fallback for unencoded legacy values


def save_credential(key_name: str, value: str):
    """Write key_name=value to ~/.rta/credentials (0o600)."""
    _ensure_rta_dir()

    # Read existing entries
    entries: dict[str, str] = {}
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    entries[k.strip()] = v.strip()

    entries[key_name] = _encode(value)

    with open(CREDENTIALS_FILE, "w") as f:
        for k, v in entries.items():
            f.write(f"{k}={v}\n")

    os.chmod(CREDENTIALS_FILE, 0o600)


def load_credential(key_name: str) -> str | None:
    """Read key_name from ~/.rta/credentials. Returns None if missing."""
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    with open(CREDENTIALS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key_name:
                    return _decode(v.strip())
    return None


def delete_credential(key_name: str):
    """Remove a specific key from ~/.rta/credentials."""
    if not os.path.exists(CREDENTIALS_FILE):
        return
    entries: dict[str, str] = {}
    with open(CREDENTIALS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() != key_name:
                    entries[k.strip()] = v.strip()
    with open(CREDENTIALS_FILE, "w") as f:
        for k, v in entries.items():
            f.write(f"{k}={v}\n")
    os.chmod(CREDENTIALS_FILE, 0o600)


def get_device_id() -> str:
    """Return stable device UUID, creating it on first call."""
    _ensure_rta_dir()
    if os.path.exists(DEVICE_ID_FILE):
        with open(DEVICE_ID_FILE, "r") as f:
            did = f.read().strip()
            if did:
                return did

    did = str(uuid.uuid4())
    with open(DEVICE_ID_FILE, "w") as f:
        f.write(did)
    os.chmod(DEVICE_ID_FILE, 0o600)
    return did
