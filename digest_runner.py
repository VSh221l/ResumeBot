# digest_runner.py
import asyncio
from core.settings.settings import settings
from core.utils.utils import logger
from services.db import list_channels
from services.summarize import summarize_text_async
from aiogram import Bot
from telethon import TelegramClient
from telethon.sessions import StringSession

import aiohttp  # for sending via bot HTTP API if needed
import os

async def fetch_telethon_session_string():
    # пример: читать из Yandex Object Storage или из Secret Manager
    return os.getenv("TELETHON_SESSION_STRING", "")  # или получить из OBS

async def run_digest(event, context):
    bot = Bot(token=settings.bots.bot_token)
    session_string = await fetch_telethon_session_string()
    if not session_string:
        logger.error("No Telethon session string provided.")
        return {"statusCode": 500, "body": "no session"}

    api_id = int(os.getenv("TELETHON_API_ID"))
    api_hash = os.getenv("TELETHON_API_HASH")

    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        channels = await list_channels()

        for ch in channels:
            # ch is dict: ch["url"], ch["user_id"]
            msgs = await client.get_messages(ch["url"], limit=5)
            for m in msgs:
                text = m.message or ""
                summary = await summarize_text_async(text)
                try:
                    await bot.send_message(ch["user_id"], f"Дайджест по каналу {ch['url']}:\n{summary}")
                except Exception as e:
                    logger.exception("Failed to send digest message: %s", e)
    await bot.session.close()
    return {"statusCode": 200, "body": "ok"}