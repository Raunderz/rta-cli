from ..core.types import ToolDefinition
from .arxiv import ArXivTool
from .base import BaseTool
from .bash import BashTool
from .edit import EditTool
from .find import FindTool
from .github import GitHubSearchTool
from .grep import GrepTool
from .lsp import GetDiagnosticsTool, GoToDefinitionTool
from .mcp_bridge import get_all_mcp_tools
from .memory import ForgetTool, MemorizeTool, RecallTool
from .read import ReadTool
from .refactor import RefactorPythonTool
from .semantic_search import SemanticSearchTool
from .skeleton import SkeletonTool
from .stackoverflow import StackOverflowTool
from .thinking import SequentialThinkingTool
from .web_fetch import WebFetchTool
from .web_search import DeepSearchTool, WebSearchTool
from .write import WriteTool
from .youtube import YouTubeTranscriptTool

__all__ = [
    "DEFAULT_TOOLS",
    "EXTRA_TOOLS",
    "ArXivTool",
    "BaseTool",
    "BashTool",
    "DeepSearchTool",
    "EditTool",
    "FindTool",
    "ForgetTool",
    "GetDiagnosticsTool",
    "GitHubSearchTool",
    "GoToDefinitionTool",
    "GrepTool",
    "MemorizeTool",
    "ReadTool",
    "RecallTool",
    "RefactorPythonTool",
    "SemanticSearchTool",
    "SequentialThinkingTool",
    "SkeletonTool",
    "StackOverflowTool",
    "WebFetchTool",
    "WebSearchTool",
    "WriteTool",
    "YouTubeTranscriptTool",
    "get_tool",
    "get_tool_definitions",
    "get_tools",
    "tools_by_name",
]

all_tools = [
    ReadTool(),
    EditTool(),
    WriteTool(),
    BashTool(),
    GrepTool(),
    FindTool(),
    WebSearchTool(),
    WebFetchTool(),
    DeepSearchTool(),
    MemorizeTool(),
    RecallTool(),
    ForgetTool(),
    SequentialThinkingTool(),
    ArXivTool(),
    StackOverflowTool(),
    GitHubSearchTool(),
    YouTubeTranscriptTool(),
    GetDiagnosticsTool(),
    GoToDefinitionTool(),
    SemanticSearchTool(),
    SkeletonTool(),
    RefactorPythonTool(),
    *get_all_mcp_tools(),
]

tools_by_name: dict[str, BaseTool] = {tool.name: tool for tool in all_tools}
DEFAULT_TOOLS: list[str] = ["read", "edit", "write", "bash", "grep", "find"]
EXTRA_TOOLS: list[str] = [
    "web_search",
    "web_fetch",
    "deep_search",
    "memorize",
    "recall",
    "forget",
    "sequential_thinking",
    "arxiv_search",
    "so_search",
    "github_search",
    "youtube_transcript",
    "get_diagnostics",
    "go_to_definition",
    "semantic_search",
    "get_repo_skeleton",
    "refactor_python",
] + [t.name for t in all_tools if t.name.startswith("mcp_")]


def get_tools(names: list[str]) -> list[BaseTool]:
    return [tool for tool in all_tools if tool.name in names]


def get_tool(tool_name: str) -> BaseTool | None:
    return tools_by_name.get(tool_name)


def get_tool_definitions(tools: list[BaseTool]) -> list[ToolDefinition]:
    return [
        ToolDefinition(name=tool.name, description=tool.description, parameters=tool.params.model_json_schema())
        for tool in tools
    ]
