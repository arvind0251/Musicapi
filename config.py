import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
INDEX_CHANNEL = os.getenv("INDEX_CHANNEL", "")
STORAGE_CHANNEL = os.getenv("STORAGE_CHANNEL", "")
DOMAIN = os.getenv("DOMAIN", "localhost")
PORT = int(os.getenv("PORT", "8000"))
