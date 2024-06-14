import pytest
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from fastapi.testclient import TestClient
from north_admin import NorthAdmin, setup_admin
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from tests.models import Base, User, UserType

from .auth_provider import AdminAuthProvider
from .config import Settings
from .routes import include_user_routes
from .users import make_test_users

JWT_SECRET_KEY = "JNBjdejjn!w443@wer"
ROOT_PASSWORD = "V7alH0lla6!1AwAit1ngU!"


load_dotenv(find_dotenv())

pytestmark = [pytest.mark.anyio]


@pytest.fixture(scope="session")
async def config() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
async def async_session(
    config: Settings,
) -> AsyncSession:
    engine = create_async_engine(
        config.postgres.url,
        echo=False,
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
    )

    async with session_maker() as session:
        yield session

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
async def root_user(
    async_session: AsyncSession,
) -> User:
    return await AdminAuthProvider.make_user(
        session=async_session,
        email="root@site.local",
        name="root",
        is_active=True,
        user_type=UserType.ROOT,
        password=ROOT_PASSWORD,
    )


@pytest.fixture(scope="session")
async def users(
    async_session: AsyncSession,
) -> dict[str, dict[str, User]]:
    return await make_test_users(session=async_session)


@pytest.fixture(scope="session")
async def admin_app(
    config: Settings,
    async_session: AsyncSession,
) -> NorthAdmin:
    app = NorthAdmin(
        sqlalchemy_uri=config.postgres.url,
        jwt_secret_key="JNBjdejjn!w443@wer",
        auth_provider=AdminAuthProvider,
    )

    return include_user_routes(app)


@pytest.fixture(scope="session")
async def app(
    admin_app: NorthAdmin,
) -> FastAPI:
    app = FastAPI()

    setup_admin(
        app=app,
        admin_app=admin_app,
    )

    return app


@pytest.fixture()
async def http_client(app: FastAPI) -> TestClient:
    return TestClient(app)
