from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import Request
from fastapi.responses import ORJSONResponse
from hawk_python_sdk.errors import InvalidHawkToken, ModuleError  # type: ignore
from pydantic import BaseModel

from auth_app.src.hawk import hawk
from auth_app.src.core.logger import logstash_handler

from .config import app_config

logger = logstash_handler()


class Settings(BaseModel):
    authjwt_secret_key: str = app_config.secret_key
    authjwt_cookie_csrf_protect: bool = False
    authjwt_token_location: set = {"cookies"}
    authjwt_access_cookie_key: str = "access_token"
    authjwt_refresh_cookie_key: str = "refresh_token"
    authjwt_access_token_expires: int = app_config.access_token_expires
    authjwt_refresh_token_expires: int = app_config.refresh_token_expires


@AuthJWT.load_config
def get_config():
    return Settings()


async def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    if app_config.enable_hawk and hawk:
        try:
            hawk.send(
                event=exc,
                context={
                    "path": str(request.url),
                    "error_type": "AuthJWTException",
                },
            )
        except (InvalidHawkToken, ModuleError) as hawk_error:
            logger.error(f"Ошибка при отправке в Hawk: {hawk_error}")
    return ORJSONResponse(
        status_code=exc.status_code, content={"detail": exc.message}
    )
