from http import HTTPStatus

import pytest
from sqlalchemy import text

from tests.functional.settings import test_settings


@pytest.mark.asyncio
async def test_success_status_my_profile(
    make_request,
    logged_in_superuser,
    profiles_db,
):
    """
    Тест api собственного профиля авторизованным пользователем.
    создание пользователя.
    """
    result = await profiles_db.execute(text("SELECT COUNT(*) FROM profiles"))
    assert result.scalar() == 0, "Перед выполнением запроса таблица профилей должна быть пуста"

    body, _, _ = logged_in_superuser
    access_token = body["access_token"]
    profiles_url = test_settings.profiles_url + "api/v1/profiles/my"

    _, _, _, status, _ = await make_request(
        method="GET",
        url=profiles_url,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert status == HTTPStatus.OK

    result = await profiles_db.execute(text("SELECT COUNT(*) FROM profiles"))

    assert result.scalar() == 1, "После успешного запроса должна появиться 1 запись в таблице профилей"


@pytest.mark.asyncio
async def test_get_my_profile(fastapi_client, make_request):
    profiles_url = test_settings.profiles_url + "api/v1/profiles/my"

    _, _, _, status, _ = await make_request(
        method="GET",
        url=profiles_url,
        headers={"Authorization": "Bearer fake_token"},
    )

    assert status == HTTPStatus.OK
