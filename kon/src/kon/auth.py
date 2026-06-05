import base64
import os
import platform
import uuid


def _rta_dir() -> str:
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
    d = _rta_dir()
    os.makedirs(d, exist_ok=True)
    if platform.system() != "Windows":
        try:
            os.chmod(d, 0o700)
        except OSError:
            pass


def _set_file_perms(path: str) -> None:
    if platform.system() != "Windows":
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def _encode(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


def _decode(value: str) -> str:
    try:
        return base64.b64decode(value.encode()).decode()
    except Exception:
        return value


def save_credential(key_name: str, value: str) -> None:
    _ensure_rta_dir()
    creds = _credentials_file()
    entries: dict[str, str] = {}
    if os.path.exists(creds):
        with open(creds, encoding="utf-8") as f:
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
    creds = _credentials_file()
    if not os.path.exists(creds):
        return None
    try:
        with open(creds, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == key_name:
                        return _decode(v.strip())
    except Exception:
        pass
    return None


def delete_credential(key_name: str) -> None:
    creds = _credentials_file()
    if not os.path.exists(creds):
        return
    entries: dict[str, str] = {}
    with open(creds, encoding="utf-8") as f:
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


def get_device_id() -> str:
    _ensure_rta_dir()
    did_file = _device_id_file()
    if os.path.exists(did_file):
        try:
            with open(did_file, encoding="utf-8") as f:
                did = f.read().strip()
            if did:
                return did
        except Exception:
            pass
    did = str(uuid.uuid4())
    with open(did_file, "w", encoding="utf-8") as f:
        f.write(did)
    _set_file_perms(did_file)
    return did
