import asyncio
from typing import Any

import aiohttp
import pytest_asyncio
from multidict import CIMultiDictProxy
from yarl import URL
from fastapi.testclient import TestClient

from tests.functional.settings import redis_settings
from profiles_app.src.main import app
from .mocks import MockJWTBearer

pytest_plugins = ["db_plugin"]


@pytest_asyncio.fixture(scope="session")
def event_loop(request):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def aiohttp_session():
    async with aiohttp.ClientSession() as aiohttp_session:
        yield aiohttp_session


@pytest_asyncio.fixture(name="make_request")
async def make_request(aiohttp_session):
    async def inner(
        method: str,
        url: str,
        query_data: dict | None = None,
        json_data: dict | None = None,
        headers: dict | None = None,
    ) -> tuple[dict[str, Any], CIMultiDictProxy, URL, int]:
        async with aiohttp_session.request(
            method=method,
            url=url,
            params=query_data,
            json=json_data,
            headers=headers,
        ) as response:
            body = await response.json(content_type=None)
            headers = response.headers
            url = response.url
            status = response.status
            cookies = response.cookies
            return body, headers, url, status, cookies  # type: ignore

    return inner


@pytest_asyncio.fixture(autouse=True)
async def clear_redis_cache():
    redis_client = redis_settings.get_conn()
    await redis_client.flushdb()


@pytest_asyncio.fixture()
async def fastapi_client():
    from profiles_app.src.main import security_jwt

    app.dependency_overrides[security_jwt] = MockJWTBearer()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
