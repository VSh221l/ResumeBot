import base64
import json
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from core.handlers.handlers import router
from services.telethon_task import DummyClient
from core.settings.settings import settings
from core.utils.utils import logger

# --- Инициализация бота и диспетчера ---
bot = Bot(
    token=settings.bots.bot_token)
dp = Dispatcher()
dp.include_router(router)

# --- Telethon-заглушка ---
client = DummyClient()

# --- Асинхронная обработка одного апдейта ---async def process_event(event):
async def process_event(event):
    # Передача полученного сообщения от телеграма в бот
    # Конструкция из официальной документации aiogram для произвольного асинхронного фреймворка
    update = types.Update.model_validate(json.loads(event['body']), context={"bot": bot})
    await dp.feed_update(bot, update)

# Точка входа
async def webhook(event, context):
    # Проверка, что прилетел POST-запрос от Telegram
    if event['httpMethod'] == 'POST':
        # Вызываем коррутин изменения состояния нашего бота
        await process_event(event)
        # Возвращаем код 200 успешного выполнения
        return {'statusCode': 200, 'body': 'ok'}

    # Если метод не POST-запрос, то выдаем код ошибки 405
    return {'statusCode': 405}

# --- Локальный запуск для теста ---
if __name__ == "__main__":
    import asyncio

    async def local_test():
        await client.start()
        print("Bot ready for local testing")

        test_update = {
            "update_id": 0,
            "message": {
                "message_id": 1,
                "from": {"id": 123456, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 123456, "type": "private"},
                "date": 0,
                "text": "/start"
            }
        }
        await process_update(test_update)
        await bot.session.close()
        await client.disconnect()

    asyncio.run(local_test())