import os
import json
import sys

MAX_CHARS = 10000

def get_config_path():
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