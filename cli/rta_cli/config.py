import os
import json
import sys

MAX_CHARS = 10000

USER_CONFIG_PATH = os.path.expanduser("~/.rta/config.json")

def get_user_config():
    if os.path.exists(USER_CONFIG_PATH):
        try:
            with open(USER_CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_config(config):
    os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
    with open(USER_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def set_last_workspace(workspace):
    config = get_user_config()
    config["last_workspace"] = os.path.abspath(workspace)
    save_user_config(config)

def get_last_workspace():
    return get_user_config().get("last_workspace")

def get_config_path():
...
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'rta_cli', 'config.json')
    return os.path.join(os.path.dirname(__file__), 'config.json')

def get_config():
    path = get_config_path()
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def get_server_url():
    return get_config().get("server_url", "http://localhost:8000")