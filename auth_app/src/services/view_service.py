from pydantic import BaseModel

from auth_app.src.db.queries.base import BaseQueryService
from auth_app.src.models.choices import RequestData
from auth_app.src.schemas.entity import UserInDB
from auth_app.src.services.cache_service import RedisCacheService


class ViewService:
    def __init__(
        self,
        query_service: BaseQueryService,
        cache_service: RedisCacheService,
    ):
        self.query_service = query_service
        self.cache_service = cache_service

    async def get_by_id(self, request_data: RequestData) -> UserInDB | None:
        """Возвращает объект по id."""
        obj_id = request_data.query
        validate_model: type[BaseModel] = request_data.validate_model
        obj = await self.cache_service._obj_from_cache(
            obj_id, model=validate_model  # type: ignore
        )
        if not obj:
            obj = await self.query_service.get_by_id(
                obj_id=obj_id  # type: ignore
            )
            if not obj:
                return None
            obj = validate_model.model_validate(obj)
            await self.cache_service._put_obj_to_cache(
                obj_id, obj  # type: ignore
            )
        return obj  # type: ignore

    async def get_list(self, request_data: RequestData) -> list[BaseModel]:
        """Возвращает список обьектов с кешированием результата."""
        validate_model: type[BaseModel] = request_data.validate_model
        key = await self.cache_service.make_cache_key(
            request_data=request_data.request_type,
            sort=request_data.sort,
            page=request_data.page,
            size=request_data.size,
            query=request_data.query,
        )
        models = await self.cache_service._get_obj_list_from_cache(
            key, validate_model
        )
        if not models:
            models = await self.query_service.get_list(request_data)
            if not models:
                return []
            models = [validate_model.model_validate(obj) for obj in models]
            await self.cache_service._put_obj_list_to_cache(key, models)
        return models
