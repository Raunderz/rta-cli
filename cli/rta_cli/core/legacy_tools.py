import asyncio
import os
from typing import Optional
from pydantic import BaseModel, Field
from .tool_base import BaseTool
from .types import ToolResult


class DiscoverProjectParams(BaseModel):
    use_cache: bool = Field(
        default=True, description="Whether to use cached project info"
    )


class DiscoverProjectTool(BaseTool):
    name = "discover_project"
    description = "Automatically detect the project language, framework, test framework, linter, type checker, and build configuration."
    parameters = DiscoverProjectParams
    icon = "?"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self,
        params: DiscoverProjectParams,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> ToolResult:
        from rta_cli.discovery import discover_project

        try:
            result = await asyncio.to_thread(
                discover_project, self.working_directory, params.use_cache
            )
            return ToolResult(success=True, result=str(result))
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GetFileContentsParams(BaseModel):
    file_path: str = Field(
        description="Path to the file to read, relative to the working directory"
    )


class GetFileContentsTool(BaseTool):
    name = "get_file_contents"
    description = (
        "Reads the contents of a specified file relative to the working directory"
    )
    parameters = GetFileContentsParams
    icon = "→"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self,
        params: GetFileContentsParams,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> ToolResult:
        from rta_cli.functions.get_file_content import get_file_contents

        try:
            result = await asyncio.to_thread(
                get_file_contents, self.working_directory, params.file_path
            )
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GetFilesInfoParams(BaseModel):
    directory: Optional[str] = Field(
        default=None,
        description="Directory to list, relative to working directory (default: root)",
    )


class GetFilesInfoTool(BaseTool):
    name = "get_files_info"
    description = "Lists files in a directory with file size and directory status"
    parameters = GetFilesInfoParams
    icon = "→"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: GetFilesInfoParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.functions.get_files_info import get_files_info

        try:
            result = await asyncio.to_thread(
                get_files_info, self.working_directory, params.directory
            )
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class WriteFileParams(BaseModel):
    file_path: str = Field(
        description="Path to the file to write, relative to the working directory"
    )
    content: str = Field(description="Content to write to the file")
    overwrite: bool = Field(
        default=True, description="Whether to overwrite if file exists"
    )


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Writes content to a file. Overwrites by default."
    parameters = WriteFileParams
    icon = "+"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: WriteFileParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.functions.write_file import write_file

        try:
            result = await asyncio.to_thread(
                write_file,
                self.working_directory,
                params.file_path,
                params.content,
                params.overwrite,
            )
            if result.startswith("Error") or result.startswith("Failed"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class DeleteFileParams(BaseModel):
    file_path: str = Field(
        description="Path to the file to delete, relative to working directory"
    )


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Deletes a specified file from the working directory."
    parameters = DeleteFileParams
    icon = "✕"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: DeleteFileParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.functions.delete_file import delete_file

        try:
            result = await asyncio.to_thread(
                delete_file, self.working_directory, params.file_path
            )
            if (
                result.startswith("Error")
                or result.startswith("Cancelled")
                or result.startswith("Failed")
            ):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class CreateDirParams(BaseModel):
    dir_path: str = Field(
        description="Path to the directory to create, relative to working directory"
    )


class CreateDirTool(BaseTool):
    name = "create_dir"
    description = "Creates a directory (and parent directories if needed) relative to the working directory."
    parameters = CreateDirParams
    icon = "+"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: CreateDirParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.functions.create_dir import create_dir

        try:
            result = await asyncio.to_thread(
                create_dir, self.working_directory, params.dir_path
            )
            if result.startswith("Error") or result.startswith("Failed"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class ApplyDiffParams(BaseModel):
    diff_text: str = Field(description="The unified diff content to apply")


class ApplyDiffTool(BaseTool):
    name = "apply_diff"
    description = (
        "Applies a unified diff to one or more files in the working directory."
    )
    parameters = ApplyDiffParams
    icon = "±"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: ApplyDiffParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.functions.apply_diff import apply_diff

        try:
            result = await asyncio.to_thread(
                apply_diff, self.working_directory, params.diff_text
            )
            if result.startswith("Error") or result.startswith("Failed"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class EditFileAstParams(BaseModel):
    file_path: str = Field(description="Path to the Python file to refactor")
    action: str = Field(
        description="Refactoring action: rename_function or rename_class"
    )
    old_name: str = Field(description="Current name of the entity")
    new_name: str = Field(description="New name for the entity")


class EditFileAstTool(BaseTool):
    name = "edit_file_ast"
    description = "Perform AST-aware refactoring on a Python file (rename function, rename class)."
    parameters = EditFileAstParams
    icon = "✶"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: EditFileAstParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.functions.edit_file_ast import edit_file_ast

        try:
            result = await asyncio.to_thread(
                edit_file_ast,
                self.working_directory,
                params.file_path,
                params.action,
                old_name=params.old_name,
                new_name=params.new_name,
            )
            if result.startswith("Error") or result.startswith("Failed"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class ListSkillsParams(BaseModel):
    pass


class ListSkillsTool(BaseTool):
    name = "list_skills"
    description = "List all available specialized skills with their descriptions."
    parameters = ListSkillsParams
    icon = "!"

    async def execute(
        self, params: ListSkillsParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.functions.list_skills import list_skills

        try:
            result = await asyncio.to_thread(list_skills)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class SemanticSearchParams(BaseModel):
    query: str = Field(
        description="Natural language query (e.g., 'how is authentication handled?')"
    )
    limit: int = Field(default=5, description="Number of results to return")


class SemanticSearchTool(BaseTool):
    name = "semantic_search"
    description = "Searches the codebase for relevant snippets using natural language semantic search."
    parameters = SemanticSearchParams
    icon = "?"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: SemanticSearchParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.functions.semantic_search import semantic_search

        try:
            result = await asyncio.to_thread(
                semantic_search, self.working_directory, params.query, params.limit
            )
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GetRepoSkeletonParams(BaseModel):
    pass


class GetRepoSkeletonTool(BaseTool):
    name = "get_repo_skeleton"
    description = "Returns a markdown skeleton of the project, showing classes and functions across all files."
    parameters = GetRepoSkeletonParams
    icon = "→"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self,
        params: GetRepoSkeletonParams,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> ToolResult:
        from rta_cli.functions.get_repo_skeleton import get_repo_skeleton

        try:
            result = await asyncio.to_thread(get_repo_skeleton, self.working_directory)
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class QuestionParams(BaseModel):
    header: Optional[str] = Field(
        default=None, description="Short label for the question (max 30 chars)"
    )
    question: str = Field(description="The question to ask the user")
    options: Optional[list[str]] = Field(
        default=None, description="Optional list of choices"
    )
    multiple: bool = Field(
        default=False, description="Allow selecting multiple options"
    )


class QuestionTool(BaseTool):
    name = "question"
    description = (
        "Ask the user a clarifying question to get more details or confirm decisions."
    )
    parameters = QuestionParams
    icon = "?"

    async def execute(
        self, params: QuestionParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.questions import ask_question
        from rta_cli.utils import get_working_directory

        try:
            wd = get_working_directory()
            result = await asyncio.to_thread(
                ask_question,
                wd,
                header=params.header,
                question=params.question,
                options=params.options,
                multiple=params.multiple,
            )
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GitStatusParams(BaseModel):
    pass


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Show the working tree status (modified, staged, untracked files)."
    parameters = GitStatusParams
    icon = "●"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: GitStatusParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.git import git_status

        try:
            result = await asyncio.to_thread(git_status, self.working_directory)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GitDiffParams(BaseModel):
    staged: bool = Field(
        default=False, description="Show staged diff instead of unstaged"
    )


class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "Show changes in the working tree (diff)."
    parameters = GitDiffParams
    icon = "●"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: GitDiffParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.git import git_diff

        try:
            result = await asyncio.to_thread(
                git_diff, self.working_directory, params.staged
            )
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GitLogParams(BaseModel):
    n: int = Field(default=10, description="Number of recent commits to show")


class GitLogTool(BaseTool):
    name = "git_log"
    description = "Show recent commit history."
    parameters = GitLogParams
    icon = "●"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: GitLogParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.git import git_log

        try:
            result = await asyncio.to_thread(git_log, self.working_directory, params.n)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GitCommitParams(BaseModel):
    message: Optional[str] = Field(default=None, description="Commit message")
    auto_add: bool = Field(
        default=True, description="Auto-stage modified files before committing"
    )
    force: bool = Field(default=False, description="Skip confirmation prompt")


class GitCommitTool(BaseTool):
    name = "git_commit"
    description = "Create a commit with the staged or modified files."
    parameters = GitCommitParams
    icon = "●"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: GitCommitParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.git import git_commit

        try:
            result = await asyncio.to_thread(
                git_commit,
                self.working_directory,
                params.message,
                params.auto_add,
                params.force,
            )
            if result.startswith("Error") or result.startswith("Cancelled"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GitCreatePrParams(BaseModel):
    title: Optional[str] = Field(default=None, description="PR title")
    body: str = Field(default="", description="PR description body")
    base: str = Field(default="main", description="Base branch to merge into")


class GitCreatePrTool(BaseTool):
    name = "git_create_pr"
    description = "Create a pull request on GitHub from the current branch."
    parameters = GitCreatePrParams
    icon = "●"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: GitCreatePrParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.git import git_create_pr

        try:
            result = await asyncio.to_thread(
                git_create_pr,
                self.working_directory,
                params.title,
                params.body,
                params.base,
            )
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GitBranchParams(BaseModel):
    list: bool = Field(default=False, description="List branches")
    create: Optional[str] = Field(
        default=None, description="Name of new branch to create"
    )
    delete: Optional[str] = Field(default=None, description="Name of branch to delete")


class GitBranchTool(BaseTool):
    name = "git_branch"
    description = "List, create, or delete git branches."
    parameters = GitBranchParams
    icon = "●"

    def __init__(self, working_directory: Optional[str] = None):
        super().__init__()
        self.working_directory = working_directory or os.getcwd()

    async def execute(
        self, params: GitBranchParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.git import git_branch

        try:
            result = await asyncio.to_thread(
                git_branch,
                self.working_directory,
                params.list,
                params.create,
                params.delete,
            )
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class WebSearchParams(BaseModel):
    query: str = Field(description="The search query string")
    max_results: int = Field(default=8, description="Maximum results to return")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web using multiple free search engines (DuckDuckGo, SearXNG, Wikipedia). No API key required."
    parameters = WebSearchParams
    icon = "?"

    async def execute(
        self, params: WebSearchParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.mcp.search import web_search

        try:
            result = await asyncio.to_thread(
                web_search, params.query, params.max_results
            )
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class FetchUrlParams(BaseModel):
    url: str = Field(
        description="The full URL to fetch (must start with http:// or https://)"
    )


class FetchUrlTool(BaseTool):
    name = "fetch_url"
    description = "Download a URL and return its readable text content (title + body). Strips HTML, scripts, and styling."
    parameters = FetchUrlParams
    icon = "?"

    async def execute(
        self, params: FetchUrlParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.mcp.search import fetch_url

        try:
            result = await asyncio.to_thread(fetch_url, params.url)
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class SequentialThinkingParams(BaseModel):
    thought: str = Field(description="Your current thought or reasoning step")
    thought_number: int = Field(description="Current thought number (starts at 1)")
    total_thoughts: int = Field(description="Estimated total thoughts needed")
    next_thought_needed: bool = Field(
        description="Whether another thought step follows"
    )
    is_revision: bool = Field(
        default=False, description="Whether this revises a previous thought"
    )
    revises_thought: Optional[int] = Field(
        default=None, description="Which thought number to revise"
    )
    branch_from_thought: Optional[int] = Field(
        default=None, description="Branch a new line of reasoning from this thought"
    )
    branch_id: Optional[str] = Field(
        default=None, description="Unique ID for this reasoning branch"
    )
    needs_more_thoughts: bool = Field(
        default=True, description="Whether more thoughts are still needed"
    )


class SequentialThinkingTool(BaseTool):
    name = "sequential_thinking"
    description = "A tool for dynamic, structured, and reflective problem-solving. Use this when working through complex problems step by step."
    parameters = SequentialThinkingParams
    icon = "?"

    async def execute(
        self,
        params: SequentialThinkingParams,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> ToolResult:
        from rta_cli.mcp.sequential_thinking import sequential_thinking

        try:
            result = await asyncio.to_thread(
                sequential_thinking,
                params.thought,
                params.thought_number,
                params.total_thoughts,
                params.next_thought_needed,
                params.is_revision,
                params.revises_thought,
                params.branch_from_thought,
                params.branch_id,
                params.needs_more_thoughts,
            )
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class MemorizeParams(BaseModel):
    key: str = Field(description="Unique key for this memory")
    value: str = Field(description="The content to remember")
    tags: str = Field(default="", description="Comma-separated tags for retrieval")


class MemorizeTool(BaseTool):
    name = "memorize"
    description = "Store a fact persistently. Use for user preferences, project decisions, or any info you want to recall later."
    parameters = MemorizeParams
    icon = "!"

    async def execute(
        self, params: MemorizeParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.mcp.memory import memorize

        try:
            result = await asyncio.to_thread(
                memorize, params.key, params.value, params.tags
            )
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class RecallParams(BaseModel):
    query: str = Field(description="Search term to find matching memories")


class RecallTool(BaseTool):
    name = "recall"
    description = "Search stored memories by keyword."
    parameters = RecallParams
    icon = "!"

    async def execute(
        self, params: RecallParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.mcp.memory import recall

        try:
            result = await asyncio.to_thread(recall, params.query)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class ForgetParams(BaseModel):
    key: str = Field(description="Key of the memory to delete")


class ForgetTool(BaseTool):
    name = "forget"
    description = "Delete a specific memory by key."
    parameters = ForgetParams
    icon = "!"

    async def execute(
        self, params: ForgetParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.mcp.memory import forget

        try:
            result = await asyncio.to_thread(forget, params.key)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class ArxivSearchParams(BaseModel):
    query: str = Field(
        description="The search query (e.g., 'large language model alignment')"
    )
    max_results: int = Field(default=5, description="Maximum results to return")


class ArxivSearchTool(BaseTool):
    name = "arxiv_search"
    description = "Search ArXiv for technical and scientific papers. Returns titles, summaries, and links. Ideal for deep technical research."
    parameters = ArxivSearchParams
    icon = "?"

    async def execute(
        self, params: ArxivSearchParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.mcp.search import arxiv_search

        try:
            result = await asyncio.to_thread(
                arxiv_search, params.query, params.max_results
            )
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class SoSearchParams(BaseModel):
    query: str = Field(description="The programming-related search query")
    max_results: int = Field(default=5, description="Maximum results to return")


class SoSearchTool(BaseTool):
    name = "so_search"
    description = "Search Stack Overflow for programming-related questions and answers. Returns titles, tags, and links. Use for troubleshooting specific code issues."
    parameters = SoSearchParams
    icon = "?"

    async def execute(
        self, params: SoSearchParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.mcp.search import so_search

        try:
            result = await asyncio.to_thread(
                so_search, params.query, params.max_results
            )
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class GithubSearchParams(BaseModel):
    query: str = Field(description="The search query")
    search_type: str = Field(
        default="repositories",
        description="What to search: 'repositories', 'code', or 'issues'",
    )
    max_results: int = Field(default=5, description="Maximum results to return")


class GithubSearchTool(BaseTool):
    name = "github_search"
    description = "Search GitHub for repositories, code, or issues. Rate-limited to 60 requests/hour without authentication."
    parameters = GithubSearchParams
    icon = "?"

    async def execute(
        self, params: GithubSearchParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.mcp.search import github_search

        try:
            result = await asyncio.to_thread(
                github_search, params.query, params.search_type, params.max_results
            )
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class YoutubeTranscriptParams(BaseModel):
    video_url: str = Field(description="The full YouTube video URL")
    language: str = Field(default="en", description="Language code for subtitles")


class YoutubeTranscriptTool(BaseTool):
    name = "youtube_transcript"
    description = (
        "Fetch transcript/subtitles from a YouTube video. No API key required."
    )
    parameters = YoutubeTranscriptParams
    icon = "?"

    async def execute(
        self,
        params: YoutubeTranscriptParams,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> ToolResult:
        from rta_cli.mcp.search import youtube_transcript

        try:
            result = await asyncio.to_thread(
                youtube_transcript, params.video_url, params.language
            )
            if result.startswith("Error"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")


class DeepSearchParams(BaseModel):
    query: str = Field(description="The research query or topic to explore")
    max_results: int = Field(
        default=8, description="Maximum results to return after deduplication"
    )
    num_queries: int = Field(
        default=3, description="Number of sub-queries to generate (max: 5)"
    )


class DeepSearchTool(BaseTool):
    name = "deep_search"
    description = "Deep research search: auto-generates multiple sub-queries from your query, runs all, and deduplicates results."
    parameters = DeepSearchParams
    icon = "?"

    async def execute(
        self, params: DeepSearchParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        from rta_cli.mcp.search import deep_search

        try:
            result = await asyncio.to_thread(
                deep_search, params.query, params.max_results, params.num_queries
            )
            if result.startswith("No results"):
                return ToolResult(success=False, result=result)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=f"Error: {e}")
