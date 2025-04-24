from fastapi import Request, status
from fastapi.responses import ORJSONResponse
from hawk_python_sdk.errors import InvalidHawkToken, ModuleError  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from auth_app.src.core.logger import set_request_id
from auth_app.src.core.logger import logstash_handler


from .hawk import hawk

logger = logstash_handler()


async def before_request(request: Request, call_next):
    """Middleware для валидации X-Request-Id и его сохранения в контексте."""
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "X-Request-Id is required"},
        )

    set_request_id(request_id)

    response = await call_next(request)
    return response


class HawkMiddleware(BaseHTTPMiddleware):
    """Middleware для перехвата и обработки ошибок с отправкой их в Hawk."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            if hawk:
                try:
                    hawk.send(event=exc, context={"path": str(request.url)})
                except (InvalidHawkToken, ModuleError) as hawk_error:
                    logger.error(f"Ошибка отправки в Hawk: {hawk_error}")
            error_response = {"detail": str(exc)}
            return JSONResponse(
                status_code=500,
                content=error_response,
            )
