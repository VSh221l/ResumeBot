# Заглушки для функционала, который будет извлекать сообщения из каналов.
# Позже сюда добавим Telethon-код для подключения к каналам и сохранения новых сообщений.

# services/telethon_client.py
import asyncio
from core.utils.utils import logger

# Заглушка для Telethon-клиента
class DummyClient:
    async def start(self):
       logger.info("⚠️ Dummy Telethon client started (тестовый режим)")

    async def disconnect(self):
       logger.info("⚠️ Dummy Telethon client disconnected (тестовый режим)")

# Заглушка для функции получения топ-постов
async def get_top_posts(channel_url: str, keywords: list):
    logger.info(f"⚠️ Dummy get_top_posts called for channel {channel_url} with keywords {keywords}")
    # Возвращаем фиктивные данные
    return [
        {"text": "Пример поста 1", "link": "https://t.me/example1"},
        {"text": "Пример поста 2", "link": "https://t.me/example2"},
    ]

# Используем одну глобальную переменную client, чтобы не менять хендлеры
client = DummyClient()
