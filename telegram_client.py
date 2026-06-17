import os
import re
from pathlib import Path
from typing import Optional, Dict, List

from pyrogram import Client
from pyrogram.types import Message

from config import API_ID, API_HASH, BOT_TOKEN, INDEX_CHANNEL, STORAGE_CHANNEL, DOWNLOAD_DIR

Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def extract_storage_id(text: str) -> Optional[int]:
    m = re.search(r"ID[:\s]+(\d+)", text or "", re.IGNORECASE)
    return int(m.group(1)) if m else None

def extract_title(text: str) -> str:
    m = re.search(r"Song[:\s]+([^|]+)", text or "", re.IGNORECASE)
    return m.group(1).strip() if m else (text or "Unknown Title").strip()

def extract_artist(text: str) -> str:
    m = re.search(r"([^-]+)-\s*([^|]+)", text or "")
    return m.group(2).strip() if m else "Unknown Artist"

def extract_type(text: str) -> str:
    t = (text or "").lower()
    if "video" in t:
        return "video"
    return "audio"

async def fetch_index() -> List[Dict]:
    songs = []
    async for msg in app.get_chat_history(INDEX_CHANNEL):
        if msg.text:
            sid = extract_storage_id(msg.text)
            if sid:
                songs.append({
                    "index_id": msg.id,
                    "storage_id": sid,
                    "title": extract_title(msg.text),
                    "artist": extract_artist(msg.text),
                    "type": extract_type(msg.text),
                    "caption": msg.text
                })
    return songs

async def get_storage_message(storage_id: int) -> Optional[Message]:
    async for msg in app.get_chat_history(STORAGE_CHANNEL, offset_id=storage_id - 1, limit=50):
        if msg.id == storage_id:
            return msg
    return None

async def upload_to_storage(file_path: str, song_type: str, title: str, artist: str) -> Optional[int]:
    caption = f"Song: {title} - {artist} | type: {song_type}"
    if song_type == "video":
        sent = await app.send_video(
            STORAGE_CHANNEL,
            video=file_path,
            caption=caption
        )
    else:
        sent = await app.send_audio(
            STORAGE_CHANNEL,
            audio=file_path,
            caption=caption
        )
    return sent.id if sent else None

async def add_to_index(storage_id: int, title: str, artist: str, song_type: str) -> Optional[int]:
    text = f"Song: {title} - {artist} | ID: {storage_id} | {song_type}"
    sent = await app.send_message(INDEX_CHANNEL, text)
    return sent.id if sent else None

async def download_from_storage(storage_id: int) -> Optional[str]:
    msg = await get_storage_message(storage_id)
    if not msg or not msg.media:
        return None

    ext = "mp4" if msg.video else "mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{storage_id}.{ext}")
    if os.path.exists(file_path):
        return file_path

    downloaded = await app.download_media(msg, file_name=file_path)
    return downloaded
