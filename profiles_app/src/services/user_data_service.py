# в profiles_app пока нигде не используется, но
# могут потребоваться запросы auth_app
import asyncio
import logging
from typing import Literal
from uuid import UUID

from fastapi import HTTPException

from profiles_app.src.core.config import app_config
from profiles_app.src.services.api_client import APIClient

logger = logging.getLogger("UserDataService")


class UserDataService:
    def __init__(
        self,
        api_client: APIClient = None,
        batch_size: int = 1000,
    ) -> None:
        self.batch_size = batch_size
        self.api_client = api_client

    async def get_users_data_by_ids(self, user_ids: list[UUID]) -> list[dict]:
        user_ids = [str(user_id) for user_id in user_ids]
        batches = [
            user_ids[i : i + self.batch_size]
            for i in range(0, len(user_ids), self.batch_size)
        ]

        tasks = [
            self.api_client.request(
                "POST", app_config.auth_url_bulk_users, json={"user_ids": batch}
            )
            for batch in batches
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for result in results:
            if isinstance(result, HTTPException):
                logger.error(f"Ошибка запроса: {result.detail}")
            elif isinstance(result, Exception):
                logger.error(f"Неизвестная ошибка: {str(result)}")
            else:
                valid_results.extend(result)

        return valid_results

    async def get_all_users_data(
        self, page: int = 1, limit: int = 1000
    ) -> list[dict]:
        results = []
        while True:
            try:
                response = await self.api_client.request(
                    "GET",
                    app_config.auth_url_all_users,
                    params={"page_number": page, "page_size": limit},
                )
            except HTTPException as e:
                logger.error(f"Ошибка запроса: {e.detail}")
                break

            if not isinstance(response, list):
                logger.error(f"Некорректный формат ответа: {type(response)}")
                break

            results.extend(response)

            if len(response) < limit:
                break
            page += 1

        return results

    async def get_users_data(
        self, user_ids: list[UUID] | Literal["all"]
    ) -> list[dict]:
        if isinstance(user_ids, str) and user_ids == "all":
            return await self.get_all_users_data()
        elif isinstance(user_ids, list):
            return await self.get_users_data_by_ids(user_ids)
        else:
            raise ValueError("Некорректное значение аргумента user_ids")
