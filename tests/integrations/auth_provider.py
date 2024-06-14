from hashlib import sha256

from north_admin import AuthProvider, UserReturnSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.models import User, UserType


class AdminAuthProvider(AuthProvider):
    PASSWORD_SALT = "SOME_STR0NG_SALT"

    @classmethod
    def hash_password(cls, password: str) -> str:
        return sha256(
            f"{cls.PASSWORD_SALT}{password}".encode(),
        ).hexdigest()

    @classmethod
    async def make_user(
        cls,
        session: AsyncSession,
        email: str,
        name: str,
        password: str,
        *,
        is_active: bool,
        user_type: UserType,
    ) -> User:
        user = User(
            email=email,
            fullname=name,
            password=cls.hash_password(password),
            user_type=user_type,
            is_active=is_active,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def login(
        self,
        session: AsyncSession,
        login: str,
        password: str,
    ) -> User | None:
        query = (
            select(User)
            .filter(User.email == login)
            .filter(User.user_type.in_([UserType.ROOT, UserType.ADMIN]))
            .filter(User.password == self.hash_password(password))
        )

        return await session.scalar(query)

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: int | str,
    ) -> User | None:
        query = (
            select(User)
            .filter(User.id == user_id)
            .filter(User.user_type.in_([UserType.ROOT, UserType.ADMIN]))
        )

        return await session.scalar(query)

    async def to_user_schema(
        self,
        user: User,
    ) -> UserReturnSchema:
        return UserReturnSchema(
            id=user.id,
            login=user.email,
            fullname=user.fullname,
        )
