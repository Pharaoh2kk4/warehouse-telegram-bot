import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ALLOWED_USERS = {
    int(user_id.strip())
    for user_id in os.getenv("ALLOWED_USERS", "").split(",")
    if user_id.strip().isdigit()
}

if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
    raise ValueError("BOT_TOKEN is missing in .env")

if not ALLOWED_USERS:
    raise ValueError("ALLOWED_USERS is missing in .env")