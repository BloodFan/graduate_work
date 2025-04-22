from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import ORJSONResponse

from profiles_app.src.services.access_service import security_jwt

from .api.v1 import favorites, profiles, reviews
from .core import config
from .db.redis import get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    redis = await get_redis()
    try:
        yield
    finally:
        await redis.close()


app = FastAPI(
    title=str(config.app_config.project_profiles_name),
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    version="1.0.0",
    description=str(config.app_config.project_profiles_description),
    contact=config.contact_config.model_dump(),  # type: ignore
    lifespan=lifespan,
)


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
