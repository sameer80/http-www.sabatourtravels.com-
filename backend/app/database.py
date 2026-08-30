from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        if settings.database_url.startswith("postgresql"):
            try:
                await conn.execute(
                    __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
                )
            except Exception:
                pass
        await conn.run_sync(Base.metadata.create_all)
        if settings.database_url.startswith("sqlite"):
            await _ensure_sqlite_columns(conn)


SQLITE_COLUMN_PATCHES = [
    ("websites", "positioning", "VARCHAR(500) DEFAULT ''"),
    ("websites", "seo_focus", "VARCHAR(500) DEFAULT ''"),
    ("websites", "sitemap_url", "VARCHAR(1000)"),
    ("rank_history", "previous_position", "FLOAT"),
    ("rank_history", "position_change", "FLOAT"),
    ("rank_history", "search_volume", "INTEGER DEFAULT 0"),
    ("rank_history", "keyword_difficulty", "FLOAT DEFAULT 0"),
    ("rank_history", "ranking_url", "VARCHAR(1000)"),
    ("rank_history", "intent", "VARCHAR(100)"),
    ("rank_history", "priority", "VARCHAR(50)"),
]


async def _ensure_sqlite_columns(conn) -> None:
    from sqlalchemy import text

    for table, column, definition in SQLITE_COLUMN_PATCHES:
        result = await conn.execute(text(f"PRAGMA table_info({table})"))
        existing = {row[1] for row in result.fetchall()}
        if column not in existing:
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
