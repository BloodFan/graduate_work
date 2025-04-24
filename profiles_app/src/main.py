from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from profiles_app.src.middleware import HawkMiddleware, before_request
from profiles_app.src.services.access_service import security_jwt

from .api.v1 import favorites, profiles, reviews
from .core import config
from .db.redis import get_redis
from .hawk import init_hawk
from .exceptions import http_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    redis = await get_redis()
    if config.app_config.enable_hawk:
        app.state.hawk = init_hawk()
    else:
        app.state.hawk = None
    try:
        yield
    finally:
        await redis.aclose()


app = FastAPI(
    title=config.app_config.project_profiles_name,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    version="1.0.0",
    description=config.app_config.project_profiles_description,
    contact=config.contact_config.model_dump(),  # type: ignore
    lifespan=lifespan,
)

app.middleware("http")(before_request)  # jaeger
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
if config.app_config.enable_hawk:
    app.add_middleware(HawkMiddleware)

app.include_router(
    profiles.router,
    prefix="/api/v1/profiles",
    tags=["profiles"],
    dependencies=[Depends(security_jwt)],
)

app.include_router(
    favorites.router,
    prefix="/api/v1/favorites",
    tags=["favorites"],
    dependencies=[Depends(security_jwt)],
)

app.include_router(
    reviews.router,
    prefix="/api/v1/reviews",
    tags=["reviews"],
    dependencies=[Depends(security_jwt)],
)
