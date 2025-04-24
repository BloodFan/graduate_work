from factory import Factory, Faker, SubFactory  # type: ignore

# from auth_app.src.db.models import Role, User, UserRoles
from tests.functional.testdata import Role, User, UserRoles


class RoleFactory(Factory):
    """Создание роли."""

    class Meta:
        model = Role

    name = Faker("word")


class UserFactory(Factory):
    """Создание Пользователя."""

    class Meta:
        model = User

    login = Faker("user_name")
    email = Faker("email")
    password = Faker("password")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    is_active = True


class UserRoleFactory(Factory):
    """Создание связи m2m User <-> Role."""

    class Meta:
        model = UserRoles

    user = SubFactory(UserFactory)
    role = SubFactory(RoleFactory)
