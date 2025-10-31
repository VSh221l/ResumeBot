# services/db.py

import time
from contextlib import asynccontextmanager
from sqlalchemy import select, Column, String, Text, Boolean, ForeignKey, AsyncAdaptedQueuePool
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core.settings.settings import settings
from core.utils.utils import logger

# YDB
# from ydb_dbapi import async_connect
# from ydb_sqlalchemy.sqlalchemy.dbapi_adapter import AdaptedAsyncConnection
from ydb_sqlalchemy.sqlalchemy.types import UInt64

Base = declarative_base()

def now_ts() -> int:
    return int(time.time())

# --- Models ---
class User(Base):
    __tablename__ = "users"
    user_id = Column(UInt64, primary_key=True, autoincrement=False)  # user_id as PK
    username = Column(String, nullable=True)
    pending_action = Column(String, nullable=True)
    pending_payload = Column(Text, nullable=True)
    created_at = Column(UInt64, default=now_ts)

    channels = relationship("Channel", back_populates="user", cascade="all, delete-orphan")

class Channel(Base):
    __tablename__ = "channels"
    id = Column(UInt64, primary_key=True, autoincrement=True)
    user_id = Column(UInt64, ForeignKey("users.user_id"))
    url = Column(String, nullable=False)
    keywords = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(UInt64, default=now_ts)

    user = relationship("User", back_populates="channels")

class SummaryLog(Base):
    __tablename__ = "summaries_log"
    id = Column(UInt64, primary_key=True, autoincrement=False)
    user_id = Column(UInt64, nullable=False)
    original_text = Column(Text, nullable=False)
    summary_text = Column(Text, nullable=False)
    created_at = Column(UInt64, default=now_ts)


# --- Connection ---
DB_URL = settings.ydb.connection_url
DB_ARGS = settings.ydb.connection_args

SessionLocal = None
async def init_session():
    """
    Ленивая инициализация подключения.
    """
    global SessionLocal
    if SessionLocal is not None:
        return

    try:
        engine = create_async_engine(DB_URL, **DB_ARGS, poolclass=AsyncAdaptedQueuePool)
        SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
        logger.info("✅ Connected to YDB")
    except Exception as e:
        logger.error(f"❌ Failed to connect to YDB: {e}")
        raise

# @contextmanager   
# def get_session():
#     """
#     Синхронный доступ к сессии — для функций, где async не используется.
#     """
#     if SessionLocal is None:
#         init_session()
#     session = SessionLocal()
#     try:
#         yield session
#         session.commit()
#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         session.close()

@asynccontextmanager
async def async_get_session():
    if SessionLocal is None:
        await init_session()
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# # --- ORM CRUD functions ---
# def ensure_user(user_id: int, username: str | None):
#     with get_session() as s:
#         u = s.get(User, user_id)
#         if u:
#             return u
#         u = User(user_id=user_id, username=username or "", created_at=now_ts())
#         s.add(u)
#         s.commit()
#         return u

# def set_pending_action(user_id: int, action: str, payload: str | None = None):
#     with get_session() as s:
#         u = s.get(User, user_id)
#         if not u:
#             u = User(user_id=user_id, username="", created_at=now_ts())
#             s.add(u)
#         u.pending_action = action
#         u.pending_payload = payload
#         s.add(u)

# def clear_pending_action(user_id: int):
#     with get_session() as s:
#         u = s.get(User, user_id)
#         if u:
#             u.pending_action = None
#             u.pending_payload = None
#             s.add(u)

# def add_channel_for_user(user_id: int, url: str, keywords: list[str]):
#     with get_session() as s:
#         u = s.get(User, user_id)
#         if not u:
#             raise ValueError("User not found")
#         ch = Channel(user=u, url=url, keywords=",".join(keywords), active=True, created_at=now_ts())
#         s.add(ch)
#         return ch

# def list_channels():
#     with get_session() as s:
#         result = s.execute(select(Channel).where(Channel.active == True))
#         channels_objs = result.scalars().all()
#         channels = [
#             {
#                 "id": ch.id,
#                 "user_id": ch.user_id,
#                 "url": ch.url,
#                 "keywords": ch.keywords.split(",") if ch.keywords else []
#             }
#             for ch in channels_objs
#         ]
#         return channels

# def save_summary(session_or_tg_id, user_id=None, original=None, summary=None):
#     if isinstance(session_or_tg_id, SessionLocal().__class__):
#         session = session_or_tg_id
#         rec = SummaryLog(
#             id=int(now_ts() * 1000),
#             user_id=user_id,
#             original_text=original,
#             summary_text=summary,
#             created_at=now_ts()
#         )
#         session.add(rec)
#         session.commit()
#         return rec
#     else:
#         _tg = session_or_tg_id
#         _orig = original
#         _summ = summary
#         with get_session() as s:
#             rec = SummaryLog(
#                 id=int(now_ts() * 1000),
#                 user_id=_tg,
#                 original_text=_orig,
#                 summary_text=_summ,
#                 created_at=now_ts()
#             )
#             s.add(rec)
#             return rec

# ensure_user
async def ensure_user(user_id: int, username: str | None):
    async with async_get_session() as s:
        u = await s.get(User, user_id)
        if u:
            return u
        u = User(user_id=user_id, username=username or "", created_at=now_ts())
        s.add(u)
        await s.commit()
        return u

# set_pending_action
async def set_pending_action(user_id: int, action: str, payload: str | None = None):
    async with async_get_session() as s:
        u = await s.get(User, user_id)
        if not u:
            u = User(user_id=user_id, username="", created_at=now_ts())
            s.add(u)
        u.pending_action = action
        u.pending_payload = payload
        s.add(u)
        await s.commit()

# clear_pending_action
async def clear_pending_action(user_id: int):
    async with async_get_session() as s:
        u = await s.get(User, user_id)
        if u:
            u.pending_action = None
            u.pending_payload = None
            s.add(u)
            await s.commit()

# add_channel_for_user
async def add_channel_for_user(user_id: int, url: str, keywords: list[str]):
    async with async_get_session() as s:
        u = await s.get(User, user_id)
        if not u:
            raise ValueError("User not found")
        ch = Channel(user=u, url=url, keywords=",".join(keywords), active=True, created_at=now_ts())
        s.add(ch)
        await s.commit()
        return ch

# list_channels
async def list_channels():
    async with async_get_session() as s:
        result = await s.execute(select(Channel).where(Channel.active == True))
        channels_objs = result.scalars().all()
        channels = [
            {
                "id": ch.id,
                "user_id": ch.user_id,
                "url": ch.url,
                "keywords": ch.keywords.split(",") if ch.keywords else []
            }
            for ch in channels_objs
        ]
        return channels


# save_summary
async def save_summary(user_id: int, original: str, summary: str):
    async with async_get_session() as s:
        return await inner_save_summary(s, user_id, original, summary)


async def inner_save_summary(session: AsyncSession, user_id: int, original: str, summary: str):
    rec = SummaryLog(
        id=int(now_ts() * 1000),
        user_id=user_id,
        original_text=original,
        summary_text=summary,
        created_at=now_ts(),
    )
    session.add(rec)
    await session.commit()
    return rec
        