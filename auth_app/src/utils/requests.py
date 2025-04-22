import asyncio
from http import HTTPStatus

import aiohttp


class HTTPException(Exception):
    def __init__(self, status_code, detail, response_text=None):
        super().__init__(f"HTTP error {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail
        self.response_text = response_text


async def aiohttp_request(
    method: str,
    url: str,
    params: dict = None,  # type: ignore
    headers: dict = None,  # type: ignore
    data: dict = None,  # type: ignore
    json: dict = None,  # type: ignore
    timeout: int = 10,  # сек
    exception_detail: str = "error request",
):
    """Обертка для асинхронных запросов."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                data=data,
                json=json,
                timeout=timeout,  # type: ignore
            ) as response:
                if response.status == HTTPStatus.OK:
                    try:
                        return await response.json()
                    except aiohttp.ContentTypeError:
                        response_text = await response.text()
                        raise HTTPException(
                            status_code=response.status,
                            detail="Invalid JSON response",
                            response_text=response_text,
                        )
                else:
                    response_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=exception_detail,
                        response_text=response_text,
                    )
        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=None, detail=f"Client error: {str(e)}"
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=None, detail="Request timeout")
