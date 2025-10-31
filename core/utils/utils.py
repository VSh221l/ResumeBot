import logging
import time

# --- Логирование ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("telegram_summarizer")

def now_ts() -> int:
    return int(time.time())

def split_into_texts(raw_text: str):
    # Парсим текст: разделяем по пустой строке или по новой строке, убираем whitespace
    parts = [p.strip() for p in raw_text.splitlines() if p.strip()]
    if not parts:
        # если не получилось — вернуть исход как единый текст
        return [raw_text.strip()]
    return parts