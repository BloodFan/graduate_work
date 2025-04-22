import asyncio

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth_app.src.core.config import superuser_data
from auth_app.src.db.models.roles import Role, UserRoles
from auth_app.src.db.models.users import User
from auth_app.src.db.sessions import get_session


async def create_superuser():
    email = superuser_data.email
    password = superuser_data.get_hashed_password
    login = superuser_data.login

    if not email or not password or not login:
        return

    async for session in get_session():  # type: ignore
        session: AsyncSession  # type: ignore
        try:
            superuser = User(
                login=login,
                email=email,
                password=password,
                first_name="Super",
                last_name="Admin",
                is_active=True,
            )
            superuser_2 = User(
                login="admin2",
                email="test2@test.com",
                password=password,
                first_name="Super",
                last_name="Admin",
                is_active=True,
            )
            superuser_3 = User(
                login="admin3",
                email="test3@test.com",
                password=password,
                first_name="Super",
                last_name="Admin",
                is_active=True,
            )
            admin_role = Role(name="admin")

            session.add(superuser)
            session.add(superuser_2)
            session.add(superuser_3)
            session.add(admin_role)
            await session.commit()

            user_role = UserRoles(user_id=superuser.id, role_id=admin_role.id)
            user_role_2 = UserRoles(
                user_id=superuser_2.id, role_id=admin_role.id
            )
            user_role_3 = UserRoles(
                user_id=superuser_3.id, role_id=admin_role.id
            )
            session.add(user_role)
            session.add(user_role_2)
            session.add(user_role_3)

            await session.commit()

        except IntegrityError:
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(create_superuser())
