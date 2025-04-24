from fastapi.security import HTTPBearer
from fastapi import Request


class MockJWTBearer(HTTPBearer):
    """Мок для авторизации JWT."""

    async def __call__(self, request: Request) -> dict:
        """
        Возвратить фиктивные данные пользователя
        вместо выполнения реального HTTP-запроса.
        """
        # Пример фиктивных данных пользователя.
        return {
            "user_id": "fake_user_id",
            "user_roles": ["user", "admin"],
            "username": "test_user",
        }
