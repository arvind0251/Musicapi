import os
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pyrogram.errors import RPCError

from config import DOMAIN, PORT
from telegram_client import (
    app as tg,
    fetch_index,
    upload_to_storage,
    add_to_index,
    download_from_storage
)
from youtube import youtube_downloader

app = FastAPI(title="Telegram Music API", version="1.0.0")

songs_db = []
Path("downloads").mkdir(exist_ok=True)

@app.on_event("startup")
async def startup():
    await tg.start()
    global songs_db
    songs_db = await fetch_index()

@app.on_event("shutdown")
async def shutdown():
    await tg.stop()

@app.get("/")
async def root():
    return {
        "message": "Telegram Music API",
        "domain": DOMAIN,
        "port": PORT
    }

@app.post("/refresh")
async def refresh():
    global songs_db
    songs_db = await fetch_index()
    return {"ok": True, "total": len(songs_db)}

@app.get("/songs")
async def all_songs():
    return {"total": len(songs_db), "songs": songs_db}

@app.get("/search")
async def search(q: str):
    result = [
        s for s in songs_db
        if q.lower() in s["title"].lower() or q.lower() in s["artist"].lower()
    ]
    return {"query": q, "total": len(result), "results": result}

@app.get("/play/{storage_id}")
async def play(storage_id: int):
    song = next((s for s in songs_db if s["storage_id"] == storage_id), None)
    if song:
        file_path = await download_from_storage(storage_id)
        if not file_path:
            raise HTTPException(404, "Telegram file not found")
        return {
            "source": "telegram",
            "title": song["title"],
            "artist": song["artist"],
            "type": song["type"],
            "url": f"/download/{storage_id}"
        }

    raise HTTPException(404, "Not found in index")

@app.get("/download/{storage_id}")
async def download(storage_id: int):
    song = next((s for s in songs_db if s["storage_id"] == storage_id), None)
    if not song:
        raise HTTPException(404, "Song not found")

    file_path = await download_from_storage(storage_id)
    if not file_path:
        raise HTTPException(404, "File not available in storage")

    ext = "mp4" if song["type"] == "video" else "mp3"
    return FileResponse(
        file_path,
        filename=f"{song['title']}-{song['artist']}.{ext}"
    )

@app.post("/fallback/youtube")
async def fallback_youtube(q: str, song_type: str = "audio", background_tasks: BackgroundTasks = None):
    query = q.strip()
    if not query:
        raise HTTPException(400, "query required")

    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    downloaded = await youtube_downloader.download(search_url, video=(song_type == "video"))
    if not downloaded:
        raise HTTPException(500, "YouTube download failed")

    title = query
    artist = "Unknown"
    song_type = "video" if song_type == "video" else "audio"

    try:
        storage_id = await upload_to_storage(downloaded, song_type, title, artist)
        if not storage_id:
            raise HTTPException(500, "Upload to storage failed")

        index_id = await add_to_index(storage_id, title, artist, song_type)
        songs_db.append({
            "index_id": index_id,
            "storage_id": storage_id,
            "title": title,
            "artist": artist,
            "type": song_type,
            "caption": f"Song: {title} - {artist} | ID: {storage_id} | {song_type}"
        })

        return {
            "ok": True,
            "source": "youtube",
            "storage_id": storage_id,
            "index_id": index_id,
            "download_url": f"http://{DOMAIN}:{PORT}/download/{storage_id}"
        }
    except RPCError as e:
        raise HTTPException(500, f"Telegram upload failed: {e}")
