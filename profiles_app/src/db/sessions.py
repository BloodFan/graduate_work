from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session

from profiles_app.src.core.config import psql_data

engine = create_async_engine(
    url=psql_data.get_dsn_for_sqlalchemy,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:  # type: ignore
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


SessionDep = Annotated[Session, Depends(get_session)]


class SessionManager:
    """Централизованное управление асинхронными сессиями."""

    def __init__(self, session_maker=async_session):
        self._session_maker = session_maker

    async def __aenter__(self):
        self.session = self._session_maker()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()

    async def get_session(self):
        """Асинхронная генерация сессии."""
        async with self._session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
