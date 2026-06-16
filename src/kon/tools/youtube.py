import asyncio
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from pydantic import BaseModel, Field

from ..core.types import ToolResult
from .base import BaseTool


class YouTubeTranscriptParams(BaseModel):
    video_url: str = Field(..., description="The full YouTube video URL (e.g., 'https://www.youtube.com/watch?v=...')")
    language: str = Field("en", description="Language code for subtitles (default: 'en')")


class YouTubeTranscriptTool(BaseTool[YouTubeTranscriptParams]):
    name = "youtube_transcript"
    params = YouTubeTranscriptParams
    description = "Fetch transcript/subtitles from a YouTube video. No API key required. Returns timestamped text. Use for extracting content from tutorial videos, lectures, and talks."
    mutating = False
    tool_icon = "🎬"

    async def execute(
        self, params: YouTubeTranscriptParams, cwd: str, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:

        video_id = self._extract_youtube_id(params.video_url)
        if not video_id:
            return ToolResult(success=False, result="Error: Could not extract YouTube video ID from URL.")

        try:
            api_url = f"https://youtubetranscript.com/api?vid={video_id}&lang={params.language}"

            loop = asyncio.get_event_loop()

            def _fetch():
                req = urllib.request.Request(api_url, headers={"User-Agent": "kon-agent"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            data = await loop.run_in_executor(None, _fetch)

            if not data:
                return ToolResult(success=True, result="No transcript available for this video.")

            lines = []
            for entry in data:
                text = entry.get("text", "")
                if text.strip():
                    start = entry.get("start", 0)
                    minutes = int(start // 60)
                    seconds = int(start % 60)
                    timestamp = f"[{minutes:02d}:{seconds:02d}]"
                    lines.append(f"{timestamp} {text}")

            if not lines:
                return ToolResult(success=True, result="No transcript available for this video.")

            output = f"Transcript for video: {params.video_url}\n\n" + "\n".join(lines)
            return ToolResult(success=True, result=output.strip(), ui_summary=f"Fetched {len(lines)} lines")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ToolResult(success=False, result="No transcript available for this video.")
            return ToolResult(success=False, result=f"Error fetching transcript: HTTP {e.code}")
        except Exception as e:
            return ToolResult(success=False, result=f"Error fetching transcript: {e}")

    def _extract_youtube_id(self, url: str) -> str | None:
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})"
        ]
        for pat in patterns:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return None

    def format_call(self, params: YouTubeTranscriptParams) -> str:
        return f"{params.video_url}"
