from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from config import DOMAIN, PORT, INDEX_CHANNEL, STORAGE_CHANNEL
from telegram_client import fetch_index, get_metadata, download_media

app = FastAPI(title="Telegram Media API", version="1.0.0")

songs_db = []
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

@app.on_event("startup")
async def startup():
    global songs_db
    songs_db = await fetch_index()

@app.get("/")
async def root():
    return {
        "message": "Telegram Media API",
        "index_channel": INDEX_CHANNEL,
        "storage_channel": STORAGE_CHANNEL
    }

@app.post("/api/refresh")
async def refresh():
    global songs_db
    songs_db = await fetch_index()
    return {"ok": True, "total": len(songs_db)}

@app.get("/api/media")
async def get_all_media():
    items = []
    for song in songs_db:
        meta = await get_metadata(song)
        if meta:
            items.append(meta)
    return {"total": len(items), "media": items}

@app.get("/api/media/search")
async def search(q: str, type: str = None):
    results = []
    for song in songs_db:
        if q.lower() in song["title"].lower() or q.lower() in song["artist"].lower():
            if type and song["type"] != type:
                continue
            meta = await get_metadata(song)
            if meta:
                results.append(meta)
    return {"query": q, "total": len(results), "results": results}

@app.get("/api/media/{media_id}")
async def media_detail(media_id: int):
    song = next((s for s in songs_db if s["storage_id"] == media_id), None)
    if not song:
        raise HTTPException(status_code=404, detail="Not found")
    meta = await get_metadata(song)
    if not meta:
        raise HTTPException(status_code=404, detail="Storage file missing")
    return meta

@app.get("/api/media/{media_id}/download")
async def download(media_id: int):
    song = next((s for s in songs_db if s["storage_id"] == media_id), None)
    if not song:
        raise HTTPException(status_code=404, detail="Not found")

    file_path = await download_media(song)
    if not file_path:
        raise HTTPException(status_code=500, detail="Download failed")

    meta = await get_metadata(song)
    ext = "mp4" if song["type"] == "video" else "mp3"
    return FileResponse(
        path=file_path,
        filename=f"{meta['title']}-{meta['artist']}.{ext}",
        media_type=meta.get("mime_type", "application/octet-stream")
    )

@app.get("/api/media/{media_id}/play")
async def play(media_id: int):
    song = next((s for s in songs_db if s["storage_id"] == media_id), None)
    if not song:
        raise HTTPException(status_code=404, detail="Not found")

    meta = await get_metadata(song)
    if not meta:
        raise HTTPException(status_code=404, detail="Storage file missing")

    return {
        "media_id": media_id,
        "title": meta["title"],
        "artist": meta["artist"],
        "type": meta["type"],
        "play_url": f"http://{DOMAIN}:{PORT}/api/media/{media_id}/download",
        "mime_type": meta["mime_type"]
    }
