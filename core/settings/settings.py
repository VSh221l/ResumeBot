# core/settings.py
import os
from dataclasses import dataclass
from environs import Env

import ydb.iam

@dataclass
class Bots:
    bot_token: str

@dataclass
class YDBSettings:
    endpoint: str
    database: str
    connection_url: str
    connection_args: dict

@dataclass
class YandexGPTSettings:
    catalog_id: str
    key_id: str
    api_key: str

@dataclass
class Settings:
    bots: Bots
    ydb: YDBSettings
    yandex_gpt: YandexGPTSettings


def get_settings(env_path: str = ".env") -> Settings:
    env = Env()
    if os.path.exists(env_path):
        env.read_env(env_path)

    # читаем значения из окружения или .env
    ydb_endpoint = os.getenv("YDB_ENDPOINT") or env.str("YDB_ENDPOINT")
    ydb_database = os.getenv("YDB_DATABASE") or env.str("YDB_DATABASE")

    # формируем корректный connection URL для SQLAlchemy с YDB
    endpoint_clean = ydb_endpoint.replace("grpcs://", "")
    connection_url = (
        f"yql+ydb_async://{endpoint_clean}/{ydb_database}"
    )

    bot_token = os.getenv("API_TOKEN") or env.str("API_TOKEN")
    gpt_catalog = os.getenv("YANDEX_CATALOG_ID") or env.str("YANDEX_CATALOG_ID")
    gpt_key_id = os.getenv("YANDEX_KEY_ID") or env.str("YANDEX_KEY_ID")
    gpt_api_key = os.getenv("YANDEX_API_KEY") or env.str("YANDEX_API_KEY")
    credentials = ydb.iam.MetadataUrlCredentials()
    # параметры подключения
    args = {
        "_add_declare_for_yql_stmt_vars": True,
        "connect_args": {
            "protocol": "grpcs",
            "credentials": credentials,
        },
    }

    return Settings(
        bots=Bots(bot_token=bot_token),
        ydb=YDBSettings(
            endpoint=ydb_endpoint,
            database=ydb_database,
            connection_url=connection_url,
            connection_args=args
        ),
        yandex_gpt=YandexGPTSettings(
            catalog_id=gpt_catalog,
            key_id=gpt_key_id,
            api_key=gpt_api_key
        )
    )


# глобальная переменная для удобного импорта
settings = get_settings()