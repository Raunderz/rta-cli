from unittest.mock import MagicMock, patch

import pytest

from kon.tools.mcp_bridge import MCPTool, get_all_mcp_tools


def _make_tool_def(name="search", description="Search the web", properties=None, required=None):
    schema = {"type": "object", "properties": properties or {}, "required": required or []}
    return {"name": name, "description": description, "inputSchema": schema}


class TestMCPToolInit:
    def test_basic_init(self):
        tool = MCPTool("myserver", _make_tool_def())
        assert tool.name == "mcp_myserver_search"
        assert tool.server_name == "myserver"
        assert tool.mcp_name == "search"
        assert tool.description == "Search the web"
        assert tool.mutating is True
        assert tool.tool_icon == "🔌"

    def test_params_from_schema(self):
        props = {
            "query": {"type": "string", "description": "search query"},
            "limit": {"type": "integer", "description": "max results"},
            "verbose": {"type": "boolean"},
        }
        tool = MCPTool("srv", _make_tool_def(properties=props, required=["query"]))
        schema = tool.params.model_json_schema()
        props_out = schema["properties"]
        assert "query" in props_out
        assert "limit" in props_out
        assert "verbose" in props_out

    def test_params_optional_field_defaults_none(self):
        props = {"query": {"type": "string"}}
        tool = MCPTool("srv", _make_tool_def(properties=props))
        instance = tool.params()
        assert instance.model_dump(exclude_none=True) == {}

    def test_no_description(self):
        tool = MCPTool("srv", {"name": "x", "inputSchema": {"type": "object", "properties": {}}})
        assert tool.description == ""


class TestMCPToolExecute:
    @pytest.mark.asyncio
    async def test_execute_success_text_content(self):
        tool = MCPTool("srv", _make_tool_def(properties={"q": {"type": "string"}}, required=["q"]))
        with patch("kon.tools.mcp_bridge.call_mcp_tool") as mock_call:
            mock_call.return_value = {
                "content": [{"type": "text", "text": "result line 1"}, {"type": "text", "text": "result line 2"}]
            }
            result = await tool.execute(tool.params(q="test"))

        assert result.success is True
        assert "result line 1" in result.result
        assert "result line 2" in result.result
        assert "Executed" in result.ui_summary

    @pytest.mark.asyncio
    async def test_execute_no_output(self):
        tool = MCPTool("srv", _make_tool_def())
        with patch("kon.tools.mcp_bridge.call_mcp_tool") as mock_call:
            mock_call.return_value = None
            result = await tool.execute(tool.params())

        assert result.success is True
        assert "no output" in result.result

    @pytest.mark.asyncio
    async def test_execute_error_response(self):
        tool = MCPTool("srv", _make_tool_def())
        with patch("kon.tools.mcp_bridge.call_mcp_tool") as mock_call:
            mock_call.return_value = {"error": "something went wrong"}
            result = await tool.execute(tool.params())

        assert result.success is False
        assert "something went wrong" in result.result

    @pytest.mark.asyncio
    async def test_execute_exception(self):
        tool = MCPTool("srv", _make_tool_def())
        with patch("kon.tools.mcp_bridge.call_mcp_tool") as mock_call:
            mock_call.side_effect = ConnectionError("timeout")
            result = await tool.execute(tool.params())

        assert result.success is False
        assert "timeout" in result.result

    @pytest.mark.asyncio
    async def test_execute_non_content_dict_result(self):
        tool = MCPTool("srv", _make_tool_def())
        with patch("kon.tools.mcp_bridge.call_mcp_tool") as mock_call:
            mock_call.return_value = {"key": "value"}
            result = await tool.execute(tool.params())

        assert result.success is True
        assert '"key"' in result.result


class TestGetAllMCPTools:
    @patch("kon.tools.mcp_bridge.list_mcp_tools")
    @patch("kon.tools.mcp_bridge.load_mcp_config")
    def test_collects_tools_from_all_servers(self, mock_config, mock_list):
        mock_config.return_value = {
            "mcpServers": {
                "server_a": {"command": "x"},
                "server_b": {"command": "y"},
            }
        }
        mock_list.side_effect = lambda name: [
            {"name": f"tool_{name}", "description": f"desc {name}", "inputSchema": {"type": "object", "properties": {}}}
        ]
        tools = get_all_mcp_tools()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert "mcp_server_a_tool_server_a" in names
        assert "mcp_server_b_tool_server_b" in names

    @patch("kon.tools.mcp_bridge.list_mcp_tools")
    @patch("kon.tools.mcp_bridge.load_mcp_config")
    def test_skips_failing_servers(self, mock_config, mock_list):
        mock_config.return_value = {"mcpServers": {"bad": {"command": "x"}, "good": {"command": "y"}}}
        mock_list.side_effect = lambda name: (_ for _ in ()).throw(RuntimeError("fail")) if name == "bad" else [
            {"name": "t", "inputSchema": {"type": "object", "properties": {}}}
        ]
        tools = get_all_mcp_tools()
        assert len(tools) == 1

    @patch("kon.tools.mcp_bridge.load_mcp_config")
    def test_empty_config(self, mock_config):
        mock_config.return_value = {"mcpServers": {}}
        assert get_all_mcp_tools() == []
