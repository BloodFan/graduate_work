from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from werkzeug.security import generate_password_hash

from tests.functional.settings import (
    auth_psql_settings,
    profiles_psql_settings,
    superuser_data,
    test_settings,
)
from tests.functional.testdata import Role, User
from tests.functional.testdata.factories import (
    RoleFactory,
    UserFactory,
    UserRoleFactory,
)


class Base(DeclarativeBase):
    pass


auth_engine = create_async_engine(
    auth_psql_settings.get_dsn_for_sqlalchemy, future=True
)
profiles_engine = create_async_engine(
    profiles_psql_settings.get_dsn_for_sqlalchemy, future=True
)

auth_async_session = sessionmaker(
    auth_engine, class_=AsyncSession, expire_on_commit=False
)

profiles_async_session = sessionmaker(
    profiles_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
async def auth_db() -> AsyncGenerator[AsyncSession, None]:
    async with auth_async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def profiles_db() -> AsyncGenerator[AsyncSession, None]:
    async with profiles_async_session() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def clear_dbs(auth_db: AsyncSession, profiles_db: AsyncSession):
    """Очистка таблиц PostgreSQL(до и после теста)."""
    for table in ["users", "roles", "userroles", "sessions", "refresh_tokens"]:
        await auth_db.execute(text(f"TRUNCATE {table} CASCADE"))

    for table in ["profiles", "favorites", "reviews",]:
        await profiles_db.execute(text(f"TRUNCATE {table} CASCADE"))

    await auth_db.commit()
    await profiles_db.commit()

    yield

    for table in ["users", "roles", "userroles", "sessions", "refresh_tokens"]:
        await auth_db.execute(text(f"TRUNCATE {table} CASCADE"))

    for table in ["profiles", "favorites", "reviews",]:
        await profiles_db.execute(text(f"TRUNCATE {table} CASCADE"))

    await auth_db.commit()
    await profiles_db.commit()


@pytest_asyncio.fixture
async def create_role(auth_db: AsyncSession) -> Role:
    """Создание и возврат роли."""

    async def _create_role(name: str):
        role = RoleFactory(name=name)
        auth_db.add(role)
        try:
            await auth_db.commit()
            return role
        except IntegrityError:
            await auth_db.rollback()
            raise

    return _create_role  # type: ignore


@pytest_asyncio.fixture
async def create_user(auth_db: AsyncSession) -> User:
    """Создание и возврат пользователя."""

    async def _create_user(
        login: str = None,  # type: ignore
        email: str = None,  # type: ignore
        password: str = None,  # type: ignore
        is_active: bool = False,
    ):
        user = UserFactory(
            login=login, email=email, password=password, is_active=is_active
        )
        auth_db.add(user)
        try:
            await auth_db.commit()
            return user
        except IntegrityError:
            await auth_db.rollback()
            raise

    return _create_user  # type: ignore


@pytest_asyncio.fixture
async def assign_role_to_user(auth_db: AsyncSession) -> None:
    """Создание связи m2m User <-> Role."""

    async def _assign_role_to_user(user: User, role: Role):
        user_role = UserRoleFactory(user=user, role=role)
        auth_db.add(user_role)
        try:
            await auth_db.commit()
        except IntegrityError:
            await auth_db.rollback()
            raise

    return _assign_role_to_user  # type: ignore


@pytest_asyncio.fixture
async def create_test_role(create_role) -> None:
    await create_role("test_role")


@pytest_asyncio.fixture
async def create_superuser(
    create_user, create_role, assign_role_to_user
) -> None:
    """Создание суперпользователя."""
    user = await create_user(
        login=superuser_data.login,
        email=superuser_data.email,
        password=superuser_data.get_hashed_password,
        is_active=True,
    )

    admin_role = await create_role("admin")

    await assign_role_to_user(user, admin_role)


@pytest_asyncio.fixture
async def create_active_user(create_user) -> User:
    """Создание активного пользователя без прав доступа."""
    return await create_user(
        login="user_active",
        email="user_active@test.com",
        password=generate_password_hash("no_matter"),
        is_active=True,
    )


@pytest_asyncio.fixture
async def create_inactive_user(create_user) -> None:
    """Создание НЕактивного пользователя без прав доступа."""
    await create_user(
        login="user_inactive",
        email="user_inactive@test.com",
        password=generate_password_hash("no_matter"),
        is_active=False,
    )


@pytest_asyncio.fixture
async def logged_in_user(create_active_user, make_request):
    """логинит актив пользователя, возвращает его токены."""
    login_url = test_settings.service_url + "api/v1/auth/login"

    login_data = {"login": "user_active", "password": "no_matter"}
    _, _, _, status, cookies = await make_request(
        method="POST", url=login_url, json_data=login_data
    )

    return cookies["access_token"], cookies["refresh_token"]


@pytest_asyncio.fixture
async def logged_in_superuser(create_superuser, make_request):
    """логинит superuser, возвращает его токены."""
    login_url = test_settings.service_url + "api/v1/auth/login"

    login_data = {
        "login": superuser_data.login,
        "password": superuser_data.password,
    }
    body, _, _, _, cookies = await make_request(
        method="POST", url=login_url, json_data=login_data
    )

    return body, cookies["access_token"], cookies["refresh_token"]


@pytest_asyncio.fixture
async def create_10_random_user(auth_db: AsyncSession) -> User:  # type: ignore
    """Создание 10 случайных пользователей."""
    for _ in range(10):
        user = UserFactory()
        auth_db.add(user)
        try:
            await auth_db.commit()
        except IntegrityError:
            await auth_db.rollback()
            raise
