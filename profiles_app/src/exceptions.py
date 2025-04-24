from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Обработка HTTP-ошибок, отдельно от других."""
    hawk = request.app.state.hawk
    if hawk is not None:
        try:
            body = await request.body()
            body_str = body.decode("utf-8") if body else None
        except Exception:
            body_str = None

        hawk.send(
            exc,
            context={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
                "method": request.method,
                "query": str(request.query_params),
                "headers": dict(request.headers),
                "body": body_str,
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "exception_type": exc.__class__.__name__,
            "message": str(exc),
        },
    )
