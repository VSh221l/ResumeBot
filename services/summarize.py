# services/summarize.py
import asyncio
import httpx
from core.settings.settings import settings

from core.utils.utils import logger

# Берём ключи и каталог через универсальные настройки
API_KEY = settings.yandex_gpt.api_key
CATALOG_ID = settings.yandex_gpt.catalog_id
BASE_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1"

SYSTEM_PROMPT = (
    "Ты выполняешь задачу аннотирования поступающих текстов. "
    "Резюмируй в 1-2 коротких предложения, затем отдельной строкой 5-7 ключевых слов."
)


async def _poll_operation(client: httpx.AsyncClient, operation_id: str, timeout: int = 20):
    """Ожидание завершения асинхронной операции YandexGPT."""
    op_url = f"https://operation.api.cloud.yandex.net/operations/{operation_id}"
    for _ in range(timeout):
        r = await client.get(op_url, headers={"Authorization": f"Api-Key {API_KEY}"})
        r.raise_for_status()
        data = r.json()
        if data.get("done"):
            return data
        await asyncio.sleep(1)
    raise TimeoutError("Timeout waiting for Yandex operation")


async def summarize_text_async(text: str) -> str:
    """Асинхронное резюмирование текста через YandexGPT."""
    prompt = {
        "modelUri": f"gpt://{CATALOG_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.2,
            "maxTokens": 1000
        },
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": text},
        ],
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Api-Key {API_KEY}"}

    timeout = httpx.Timeout(30.0)  # 30 секунд на весь запрос
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            # Запрос на создание асинхронной операции
            r = await client.post(f"{BASE_URL}/completionAsync", headers=headers, json=prompt)
            r.raise_for_status()
            op_id = r.json().get("id")
            if not op_id:
                raise RuntimeError("Не удалось получить operation id от YandexGPT")

            # Ожидаем завершения операции
            res = await _poll_operation(client, op_id)
            summary = (
                res.get("response", {})
                .get("alternatives", [{}])[0]
                .get("message", {})
                .get("text", "")
            )
            return summary.strip()
        
        except httpx.TimeoutException:
            logger.error("Timeout при обращении к YandexGPT")
            return "⚠️ Ошибка: сервис не ответил вовремя."
        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка API: {e.response.status_code} {e.response.text}")
            return "⚠️ Ошибка при обращении к API YandexGPT."
        except Exception as e:
            logger.exception(f"Непредвиденная ошибка: {e}")
            return "⚠️ Ошибка обработки текста."