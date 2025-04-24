from fastapi import Request, status
from fastapi.responses import ORJSONResponse
from hawk_python_sdk.errors import InvalidHawkToken, ModuleError  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from profiles_app.src.core.logger import set_request_id
from profiles_app.src.core.logger import logstash_handler


logger = logstash_handler()


async def before_request(request: Request, call_next):
    """Middleware для валидации X-Request-Id и его сохранения в контексте."""
    try:
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )

        set_request_id(request_id)

        response = await call_next(request)
        return response
    except BaseExceptionGroup as errors:
        raise errors
    except Exception as e:
        raise e


class HawkMiddleware(BaseHTTPMiddleware):
    """Middleware для перехвата и обработки ошибок с отправкой их в Hawk."""

    async def dispatch(self, request: Request, call_next):
        hawk = request.app.state.hawk
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            if hawk is not None:
                try:
                    body = await request.body()
                    body_str = body.decode("utf-8") if body else None
                    hawk.send(
                        exc,
                        context={
                            "path": request.url.path,
                            "method": request.method,
                            "query": str(request.query_params),
                            "headers": dict(request.headers),
                            "body": body_str,
                        },
                    )
                except (InvalidHawkToken, ModuleError) as hawk_error:
                    logger.error(f"Ошибка отправки в Hawk: {hawk_error}")
            error_response = {"detail": str(exc)}
            logger.error(f"Error: {str(exc)}")
            return JSONResponse(
                status_code=500,
                content=error_response,
            )
