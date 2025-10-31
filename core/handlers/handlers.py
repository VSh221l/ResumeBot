# core/handlers/handlers.py
from aiogram import Router, F
from aiogram.types import Message
from services.db import (
    add_channel_for_user,
    list_channels,
    save_summary,
    ensure_user
)
from services.summarize import summarize_text_async
from services.telethon_task import get_top_posts, DummyClient

router = Router()
client = DummyClient()  # пока заглушка, для serverless Telethon-запуск можно позже

# --- /start ---
@router.message(F.text == "/start")
async def start_cmd(message: Message):
    await ensure_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "Привет! Используй:\n"
        "/add_channel <ссылка или @username> | ключевое слово1, ключевое слово2 — добавить канал\n"
        "/summarize <текст> — получить резюме текста\n"
    )


# --- /add_channel ---
@router.message(F.text.startswith("/add_channel"))
async def add_channel(message: Message):
    try:
        parts = message.text.split(" ", 1)
        if len(parts) != 2 or "|" not in parts[1]:
            await message.answer(
                "❌ Неверный формат команды.\n"
                "Пример: /add_channel @mychannel | crypto, ai, finance"
            )
            return

        channel_part, keywords_part = parts[1].split("|", 1)
        channel_url = channel_part.strip()
        keywords = [kw.strip() for kw in keywords_part.split(",") if kw.strip()]
        if not keywords:
            await message.answer("❌ Не указаны ключевые слова.")
            return

        await ensure_user(message.from_user.id, message.from_user.username)
        await add_channel_for_user(message.from_user.id, channel_url, keywords)

        await message.answer(f"✅ Канал {channel_url} добавлен с ключевыми словами: {keywords}")

    except Exception as e:
        await message.answer(f"❌ Ошибка добавления канала: {e}")


# --- /top_posts ---
@router.message(F.text == "/top_posts")
async def top_posts(message: Message):
    try:
        channels = await list_channels()
        user_channels = [ch for ch in channels if ch["user_id"] == message.from_user.id]

        if not user_channels:
            await message.answer("❌ У тебя нет добавленных каналов. Используй /add_channel.")
            return

        result_text = "📌 *Топ постов:*\n\n"
        await client.start()
        for ch in channels:
            posts = await get_top_posts(ch["url"], ch["keywords"])
            result_text += f"🔹 *{ch['url']}*\n"
            for p in posts:
                result_text += f"- [{p['text']}]({p['link']})\n"
            result_text += "\n"

        await message.answer(result_text, parse_mode="Markdown")
        await client.disconnect()

    except Exception as e:
        await message.answer(f"❌ Ошибка получения постов: {e}")


# --- /summarize ---
@router.message(F.text.startswith("/summarize"))
async def summarize(message: Message):
    text = message.text.replace("/summarize", "").strip()
    if not text:
        await message.answer("❌ Отправь текст после команды /summarize")
        return

    await message.answer("🔹 Обрабатываю текст...")
    try:
        summary = await summarize_text_async(text)
        await save_summary(message.from_user.id, text, summary)
        await message.answer(summary)
    except Exception as e:
        await message.answer(f"❌ Ошибка при суммаризации: {e}")