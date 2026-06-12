import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from kon.mcp import call_mcp_tool, MCP_CONFIG_PATH

def test_mcp_config_tampering(tmp_path):
    """
    Verify that MCP server executes the command specified in the config.
    This test confirms that if the config is tampered with, 
    it will execute arbitrary commands.
    """
    mock_config = {
        "mcpServers": {
            "malicious": {
                "command": "echo",
                "args": ["pwned"],
                "env": {}
            }
        }
    }
    
    # Use a temporary config path
    with patch("kon.mcp.MCP_CONFIG_PATH", tmp_path / "mcp_config.json"):
        with open(tmp_path / "mcp_config.json", "w") as f:
            json.dump(mock_config, f)
            
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stdin = MagicMock()
            mock_proc.stdout = MagicMock()
            mock_proc.stdout.readline.return_value = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"content": []}})
            mock_popen.return_value = mock_proc
            
            call_mcp_tool("malicious", "any_tool", {})
            
            # Verify it tried to execute 'echo pwned'
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            assert args[0] == ["echo", "pwned"]

def test_mcp_environment_injection(tmp_path):
    """
    Verify that environment variables in the config are passed to the subprocess.
    """
    mock_config = {
        "mcpServers": {
            "env_test": {
                "command": "test_cmd",
                "env": {"MALICIOUS_VAR": "injected"}
            }
        }
    }
    
    with patch("kon.mcp.MCP_CONFIG_PATH", tmp_path / "mcp_config.json"):
        with open(tmp_path / "mcp_config.json", "w") as f:
            json.dump(mock_config, f)
            
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stdin = MagicMock()
            mock_proc.stdout = MagicMock()
            # Return a valid response to prevent retry loop
            mock_proc.stdout.readline.return_value = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"content": []}})
            mock_popen.return_value = mock_proc
            
            call_mcp_tool("env_test", "any_tool", {})
            
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            assert kwargs["env"]["MALICIOUS_VAR"] == "injected"
