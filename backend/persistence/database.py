import os
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


_engine = None
_async_engine = None
_SessionLocal = None
_AsyncSessionLocal = None
_uses_postgres = False


def get_engine(db_path: str = "data/database/stockrec.db"):
    global _engine, _SessionLocal, _uses_postgres
    if _engine is not None:
        return _engine

    db_url = os.environ.get("DATABASE_URL", "")
    db_url_sync = os.environ.get("DATABASE_URL_SYNC", "")

    if db_url and db_url_sync:
        _uses_postgres = True
        logger.info("Using PostgreSQL database")
        _engine = create_engine(
            db_url_sync,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
    else:
        abs_path = db_path
        if not os.path.isabs(abs_path):
            abs_path = str(Path(__file__).resolve().parent.parent.parent / db_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{abs_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )

    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_async_engine():
    global _async_engine, _AsyncSessionLocal
    if _async_engine is not None:
        return _async_engine

    db_url = os.environ.get("DATABASE_URL", "")

    if db_url:
        _async_engine = create_async_engine(
            db_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
        _AsyncSessionLocal = async_sessionmaker(
            _async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _async_engine


def get_session():
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call get_engine() first.")
    return _SessionLocal()


async def get_async_session() -> AsyncSession:
    if _AsyncSessionLocal is None:
        raise RuntimeError("Async database not initialized. Call get_async_engine() first.")
    async with _AsyncSessionLocal() as session:
        yield session


def init_db(db_path: str = "data/database/stockrec.db"):
    from backend.persistence import models  # noqa: F401

    engine = get_engine(db_path)
    Base.metadata.create_all(bind=engine)
    return engine


def is_postgres() -> bool:
    return _uses_postgres
