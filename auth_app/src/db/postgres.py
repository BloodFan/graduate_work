import abc
import logging
from contextlib import asynccontextmanager
from logging import config as logging_config
from typing import AsyncGenerator

from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from auth_app.src.core.config import psql_data
from auth_app.src.core.logger import LOGGING
from auth_app.src.services.my_backoff import backoff

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("db_service")


class DBService(abc.ABC):
    """Абстрактный сервис доступа к БД (асинхронный)."""

    _engine = None
    _async_session_factory = None

    @classmethod
    def init_engine(cls, database_url: str):
        """Инициализирует асинхронный движок базы данных."""
        cls._engine = create_async_engine(database_url, future=True)
        cls._async_session_factory = sessionmaker(  # type: ignore
            cls._engine, class_=AsyncSession, expire_on_commit=False
        )


class PSQLService(DBService):
    def __init__(self, database_url: str):
        self.init_engine(database_url)

    @backoff(
        errors=(OperationalError, DBAPIError), client_errors=(InterfaceError,)
    )
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получает асинхронную сессию с подключением к базе данных."""
        if not self._async_session_factory:
            raise Exception("Session factory is not initialized.")

        async with self._async_session_factory() as session:
            yield session


async def get_psql_db_service() -> PSQLService:
    db_service = PSQLService(psql_data.get_dsn_for_sqlalchemy)
    return db_service
