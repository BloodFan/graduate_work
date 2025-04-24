import asyncio
from asyncpg import connect, exceptions
from pydantic import ValidationError

from profiles_app.src.core.logger import logstash_handler
from tests.functional.settings import (
    auth_psql_settings,
    profiles_psql_settings,
)
from profiles_app.src.services.my_backoff import backoff


logger = logstash_handler()

@backoff(
    start_sleep_time=2,
    errors=(
        exceptions.ConnectionDoesNotExistError,
        exceptions.TooManyConnectionsError,
        exceptions.PostgresConnectionError,
        ValidationError
    ),
)
async def check_postgres_connection(dsn: str):
    try:
        conn = await connect(dsn=dsn)
        await conn.close()
        return True
    except exceptions.PostgresError as e:
        logger.error(f"PostgreSQL connection error: {str(e)}")
        raise


async def wait_for_postgres():
    auth_dsn = auth_psql_settings.get_dsn_for_check

    profiles_dsn = profiles_psql_settings.get_dsn_for_check

    auth_result = await check_postgres_connection(auth_dsn)
    profiles_result = await check_postgres_connection(profiles_dsn)

    if auth_result and profiles_result:
        logger.info("Both PostgreSQL databases are ready!")
        return True
    return False


if __name__ == "__main__":
    asyncio.run(wait_for_postgres())
