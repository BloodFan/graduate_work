from types import TracebackType
from typing import Any, Type

import aiohttp

from profiles_app.src.services.token_manager import TokenManager


class HTTPException(Exception):
    def __init__(
        self,
        status_code: int | None,
        detail: str,
        response_text: str | None = None
    ) -> None:
        super().__init__(f"HTTP error {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail
        self.response_text = response_text


class APIClient:
    def __init__(
        self, base_url: str, token_manager: TokenManager | None = None
    ) -> None:
        self.base_url = base_url
        self.token_manager = token_manager
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,  # Тип исключения, если есть.
        exc: BaseException | None,            # Сам объект исключения.
        tb: TracebackType | None,             # Трассировка стека.
    ) -> bool | None:                         # Возвращает `None` или `bool`.
        if self.session:
            await self.session.close()

    async def request(self, method: str, endpoint: str, **kwargs) -> Any:
        if not self.session:
            raise RuntimeError(
                "APIClient must be used within an async context manager"
            )

        headers = {}
        if self.token_manager:
            auth_headers = await self.token_manager.get_auth_headers()
            headers.update(auth_headers)

        headers.update(kwargs.pop("headers", {}))
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                if response.status >= 400:
                    response_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail="Request error",
                        response_text=response_text,
                    )
                return await response.json()
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=None, detail=str(e))
