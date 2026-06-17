import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

INDEX_CHANNEL = os.getenv("INDEX_CHANNEL", "")
STORAGE_CHANNEL = os.getenv("STORAGE_CHANNEL", "")

DOMAIN = os.getenv("DOMAIN", "localhost")
PORT = int(os.getenv("PORT", "8000"))

ENABLE_YTDLP = os.getenv("ENABLE_YTDLP", "true").lower() == "true"
ENABLE_COOKIES = os.getenv("ENABLE_COOKIES", "true").lower() == "true"
COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies/cookies.txt")

VIDEO_MAX_HEIGHT = int(os.getenv("VIDEO_MAX_HEIGHT", "720"))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
