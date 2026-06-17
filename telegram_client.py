import re
from pathlib import Path
from telethon import TelegramClient
from config import API_ID, API_HASH, INDEX_CHANNEL, STORAGE_CHANNEL

client = TelegramClient("session_name", API_ID, API_HASH)
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

def extract_storage_id(text: str):
    m = re.search(r"ID[:s]+(d+)", text or "")
    return int(m.group(1)) if m else None

def extract_title(text: str):
    m = re.search(r"Song[:s]+([^|]+)", text or "", re.IGNORECASE)
    return m.group(1).strip() if m else (text or "Unknown Title").strip()

def extract_artist(text: str):
    m = re.search(r"([^-]+)-s*([^|]+)", text or "")
    return m.group(2).strip() if m else "Unknown Artist"

def extract_type(text: str):
    t = (text or "").lower()
    if "video" in t:
        return "video"
    return "audio"

async def fetch_index():
    await client.start()
    songs = []

    async for msg in client.iter_messages(INDEX_CHANNEL):
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

async def get_storage_message(storage_id: int):
    await client.start()
    async for msg in client.iter_messages(STORAGE_CHANNEL, ids=storage_id):
        return msg
    return None

async def get_metadata(song: dict):
    msg = await get_storage_message(song["storage_id"])
    if not msg:
        return None

    media_type = song["type"]
    meta = {
        "storage_id": song["storage_id"],
        "index_id": song["index_id"],
        "title": song["title"],
        "artist": song["artist"],
        "type": media_type,
        "caption": song["caption"],
        "date": str(msg.date) if msg.date else None
    }

    if msg.audio:
        meta.update({
            "duration": msg.audio.duration or 0,
            "size": msg.audio.size or 0,
            "mime_type": "audio/mpeg"
        })
    elif msg.video:
        meta.update({
            "duration": msg.video.duration or 0,
            "size": msg.video.size or 0,
            "width": msg.video.width or 0,
            "height": msg.video.height or 0,
            "mime_type": "video/mp4"
        })
    elif msg.document:
        meta.update({
            "size": msg.document.size or 0,
            "mime_type": msg.document.mime_type or "application/octet-stream"
        })

    return meta

async def download_media(song: dict):
    msg = await get_storage_message(song["storage_id"])
    if not msg:
        return None

    if msg.audio:
        ext = "mp3"
    elif msg.video:
        ext = "mp4"
    else:
        ext = "bin"

    file_path = DOWNLOAD_DIR / f"{song['storage_id']}.{ext}"
    if file_path.exists():
        return str(file_path)

    path = await client.download_media(msg, file=str(file_path))
    return path
