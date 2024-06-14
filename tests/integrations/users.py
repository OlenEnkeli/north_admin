from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integrations.auth_provider import AdminAuthProvider
from tests.models import User, UserType


async def make_user(
    session: AsyncSession,
    *,
    is_active: bool = True,
    user_type: UserType = UserType.USER,
) -> User:
    faker = Faker()

    return await AdminAuthProvider.make_user(
        session=session,
        is_active=is_active,
        user_type=user_type,
        email=faker.email(),
        name=faker.name(),
        password=faker.password(),
    )


async def make_test_users(session: AsyncSession) -> dict[str, dict[str, User]]:
    result = {
        "active": {},
        "inactive": {},
        "admin_type": {},
        "user_type": {},
    }

    for _ in range(2):
        user = await make_user(
            session=session,
            is_active=True,
            user_type=UserType.USER,
        )

        result["active"][user.id] = user
        result["user_type"][user.id] = user

    for _ in range(2):
        user = await make_user(
            session=session,
            is_active=False,
            user_type=UserType.USER,
        )

        result["inactive"][user.id] = user
        result["user_type"][user.id] = user

    user = await make_user(
        session=session,
        is_active=True,
        user_type=UserType.ADMIN,
    )
    result["active"][user.id] = user
    result["admin_type"][user.id] = user

    user = await make_user(
        session=session,
        is_active=False,
        user_type=UserType.ADMIN,
    )
    result["inactive"][user.id] = user
    result["admin_type"][user.id] = user

    return result
