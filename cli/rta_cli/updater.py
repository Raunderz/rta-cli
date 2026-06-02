import os
import sys
import json
import hashlib
import time
import shutil
import tempfile
import subprocess
from urllib.request import urlopen, Request
from rta_cli.__init__ import __version__
from rta_cli.ui import Console

VERSION_URL = "https://rta-three.vercel.app/version.json"
CHECK_INTERVAL = 86400  # 24 hours between checks
console = Console()

def check_startup_update():
    """Silent update check on CLI startup. Runs at most once per 24h."""
    check_file = os.path.expanduser("~/.rta/last_update_check")
    now = time.time()
    try:
        if os.path.exists(check_file):
            with open(check_file) as f:
                last_check = float(f.read().strip())
            if now - last_check < CHECK_INTERVAL:
                return
    except (ValueError, OSError):
        pass
    try:
        req = Request(VERSION_URL, headers={"User-Agent": "rta-cli-updater"}, method="GET")
        with urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
        latest = data.get("version", "")
        if latest and latest != __version__:
            msg = f"\x1b[33mUpdate available: v{latest} (current: v{__version__}). Run 'rta update' to upgrade.\x1b[0m\n"
            sys.stderr.write(msg)
            sys.stderr.flush()
    except Exception:
        pass
    try:
        os.makedirs(os.path.dirname(check_file), exist_ok=True)
        with open(check_file, "w") as f:
            f.write(str(now))
    except OSError:
        pass


def get_latest_version():
    """Fetch version.json from the website."""
    try:
        req = Request(VERSION_URL, headers={"User-Agent": "rta-cli-updater"})
        with urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        console.print(f"[red]Error fetching version info: {e}[/red]")
        return None

def check_for_updates():
    """Compare current version with latest."""
    latest_info = get_latest_version()
    if not latest_info:
        return None
    
    latest_version = latest_info.get("version")
    if latest_version and latest_version != __version__:
        return latest_info
    return None

def download_file(url, dest_path):
    """Download file with a simple progress indicator."""
    try:
        req = Request(url, headers={"User-Agent": "rta-cli-updater"})
        with urlopen(req, timeout=30) as response:
            total_size = int(response.info().get('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            
            with open(dest_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    f.write(buffer)
                    if total_size:
                        percent = int(downloaded * 100 / total_size)
                        print(f"\rDownloading: {percent}%", end="", flush=True)
            print() # New line after progress
        return True
    except Exception as e:
        console.print(f"\n[red]Download failed: {e}[/red]")
        return False

def verify_sha256(file_path, expected_hash):
    """Verify file integrity."""
    if not expected_hash:
        return True # Skip if no hash provided
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest() == expected_hash

def perform_update():
    """Main update flow."""
    latest_info = check_for_updates()
    if not latest_info:
        console.print(f"[green]Rta is already up to date (v{__version__}).[/green]")
        return

    latest_version = latest_info["version"]
    console.print(f"[yellow]New version available: v{latest_version} (current: v{__version__})[/yellow]")
    
    is_windows = sys.platform.startswith("win")
    url_key = "url_windows" if is_windows else "url_linux"
    hash_key = "sha256_windows" if is_windows else "sha256_linux"
    
    url = latest_info.get(url_key)
    expected_hash = latest_info.get(hash_key)
    
    if not url:
        console.print("[red]No download URL found for your platform.[/red]")
        return

    # Use a temporary file for download
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        if not download_file(url, tmp_path):
            return

        if not verify_sha256(tmp_path, expected_hash):
            console.print("[red]Integrity check failed! The downloaded file may be corrupted.[/red]")
            return

        # Path to current executable
        current_exe = os.path.abspath(sys.executable)
        # If we are running as a python script, sys.executable is the python interpreter.
        # PyInstaller sets sys.frozen = True and sys._MEIPASS.
        if not getattr(sys, 'frozen', False):
            console.print("[yellow]Note: Not running as a standalone binary. Update logic will only download the file.[/yellow]")
            console.print(f"New binary downloaded to: {tmp_path}")
            return

        if is_windows:
            # Windows self-replacement strategy
            # Move the current exe to a .old file and move the new one in
            # This is tricky because the file is locked. 
            # We'll use a batch script to swap them after we exit.
            old_exe = current_exe + ".old"
            batch_content = f"""
@echo off
timeout /t 1 /nobreak > nul
del "{old_exe}"
move /y "{current_exe}" "{old_exe}"
move /y "{tmp_path}" "{current_exe}"
start "" "{current_exe}"
del %0
"""
            batch_path = os.path.join(tempfile.gettempdir(), "rta_update.bat")
            with open(batch_path, "w") as f:
                f.write(batch_content)
            
            subprocess.Popen(["cmd.exe", "/c", batch_path], creationflags=subprocess.CREATE_NO_WINDOW)
            console.print("[green]Update downloaded. Rta will restart shortly...[/green]")
            sys.exit(0)
        else:
            # Linux/POSIX self-replacement
            # os.rename works even if the file is open
            os.chmod(tmp_path, 0o755)
            os.rename(tmp_path, current_exe)
            console.print(f"[green]Successfully updated to v{latest_version}![/green]")
            # Re-exec to start the new version
            os.execv(current_exe, sys.argv)

    except Exception as e:
        console.print(f"[red]Update failed: {e}[/red]")
    finally:
        if not is_windows and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass
