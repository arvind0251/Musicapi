import os
import glob
import asyncio
from pathlib import Path
from typing import Optional

import yt_dlp

from config import ENABLE_YTDLP, ENABLE_COOKIES, COOKIES_FILE, DOWNLOAD_DIR, VIDEO_MAX_HEIGHT

Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path("cookies").mkdir(parents=True, exist_ok=True)

class YouTubeDownloader:
    def __init__(self):
        self.base_url = "https://www.youtube.com/watch?v="

    def _locate_file(self, video_id: str, want_video: bool = False) -> Optional[str]:
        exts_video = {".mp4", ".mkv", ".webm", ".mov"}
        exts_audio = {".mp3", ".m4a", ".opus", ".webm", ".ogg", ".wav", ".flac"}

        candidates = [
            p for p in glob.glob(f"{DOWNLOAD_DIR}/{video_id}*")
            if not p.endswith((".part", ".info.json", ".ytdl"))
        ]

        for p in candidates:
            ext = Path(p).suffix.lower()
            if want_video and ext in exts_video:
                return p
            if not want_video and ext in exts_audio:
                return p

        return candidates[0] if candidates else None

    def _build_opts(self, video: bool):
        base = {
            "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "no_warnings": True,
            "overwrites": False,
            "continuedl": True,
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "concurrent_fragment_downloads": 4,
            "http_chunk_size": 524288,
            "noprogress": True
        }

        if video:
            height_filter = f"[height<={VIDEO_MAX_HEIGHT}]" if VIDEO_MAX_HEIGHT > 0 else ""
            fmt = f"bestvideo{height_filter}+bestaudio/best"
            return {
                **base,
                "format": fmt,
                "merge_output_format": "mp4",
            }

        return {
            **base,
            "format": "bestaudio[ext=m4a]/bestaudio/best",
        }

    def _cookies(self) -> Optional[str]:
        if ENABLE_COOKIES and os.path.exists(COOKIES_FILE):
            return COOKIES_FILE
        return None

    async def download(self, youtube_url: str, video: bool = False) -> Optional[str]:
        if not ENABLE_YTDLP:
            return None

        opts = self._build_opts(video)
        cookiefile = self._cookies()
        if cookiefile:
            opts["cookiefile"] = cookiefile

        def run():
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    if not info:
                        return None
                vid = info.get("id")
                return self._locate_file(vid, want_video=video)
            except Exception:
                return None

        return await asyncio.to_thread(run)

youtube_downloader = YouTubeDownloader()
