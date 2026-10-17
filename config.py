"""Read and validate bot settings from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_settings() -> tuple[str, int]:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id_text = os.getenv("ADMIN_ID", "").strip()

    if not token:
        raise ValueError("BOT_TOKEN is missing. Set it in .env or the environment.")
    if not admin_id_text.isdecimal() or int(admin_id_text) <= 0:
        raise ValueError("ADMIN_ID must be a positive numeric Telegram user ID.")
    return token, int(admin_id_text)


BOT_TOKEN, ADMIN_ID = get_settings()
