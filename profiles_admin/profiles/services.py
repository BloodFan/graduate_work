from datetime import datetime
from typing import Any

import aiohttp
from django.conf import settings

from .utils import encode_id


class TokenManager:
    def __init__(
        self,
        service_id: str = settings.PROFILES_ADMIN_NAME,
        max_age: int = settings.SERVICE_TOKEN_MAX_AGE,
        buffer_seconds: int = 60 * 60,
    ):
        self.service_id = service_id
        self.max_age = max_age
        self.buffer_seconds = buffer_seconds
        self.token = None
        self.generated_at = None

    async def get_token(self) -> str:
        if self._is_expired():
            self.token = await encode_id(self.service_id)
            self.generated_at = datetime.now()
        return self.token

    def _is_expired(self) -> bool:
        if not self.generated_at:
            return True
        elapsed = (datetime.now() - self.generated_at).total_seconds()
        return elapsed > (self.max_age - self.buffer_seconds)

    async def get_auth_headers(self) -> dict:
        if self._is_expired():
            await self.get_token()
        return {"X-Service-Token": self.token}


class HTTPException(Exception):
    def __init__(self, status_code, detail, response_text=None):
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

    async def __aexit__(self, exc_type, exc, tb):
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
