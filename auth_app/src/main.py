from contextlib import asynccontextmanager

from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import Depends, FastAPI
from fastapi.responses import ORJSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from auth_app.src.services.access_service import security_jwt

from .api.v1 import (
    auth,
    oauth,
    reset_password,
    role,
    sessions,
    signup,
    user_roles,
    users,
)
from .core import config
from .core.auth_config import authjwt_exception_handler
from .db.redis import get_redis
from .exceptions import global_exception_handler, http_exception_handler
from .hawk import init_hawk
from .middleware import HawkMiddleware, before_request
from .tracing import configure_tracer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    redis = await get_redis()
    if config.app_config.enable_hawk:
        app.state.hawk = init_hawk()
    else:
        app.state.hawk = FileNotFoundError
    try:
        await FastAPILimiter.init(redis)
        yield
    finally:
        await redis.close()


app = FastAPI(
    title=str(config.app_config.project_auth_name),
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    version="1.0.0",
    description=str(config.app_config.project_auth_description),
    contact=config.contact_config,  # type: ignore
    lifespan=lifespan,
)

if config.app_config.enable_tracer:
    configure_tracer(app)  # jaeger
if config.app_config.enable_hawk:
    app.add_middleware(HawkMiddleware)

app.middleware("http")(before_request)  # jaeger
app.add_middleware(SessionMiddleware, secret_key=config.app_config.secret_key)
app.add_exception_handler(AuthJWTException, authjwt_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)  # type: ignore
app.add_exception_handler(
    StarletteHTTPException, http_exception_handler  # type: ignore
)

app.include_router(oauth.router, prefix="/api/v1/auth", tags=["oauth"])
app.include_router(signup.router, prefix="/api/v1/signup", tags=["signup"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"],
    dependencies=[
        Depends(security_jwt),
        Depends(RateLimiter(times=10, seconds=60)),
    ],
)
app.include_router(
    reset_password.router, prefix="/api/v1/users", tags=["users"]
)
app.include_router(sessions.router, prefix="/api/v1/users", tags=["sessions"])
app.include_router(
    role.router,
    prefix="/api/v1/roles",
    tags=["roles"],
    dependencies=[Depends(security_jwt)],
)
app.include_router(
    user_roles.router,
    prefix="/api/v1/user-roles",
    tags=["roles"],
    dependencies=[Depends(security_jwt)],
)
