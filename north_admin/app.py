from typing import Type

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from north_admin.admin_router import AdminRouter
from north_admin.auth_provider import AuthProvider
from north_admin.dto import (
    JWTTokens,
    ModelInfoDTO,
    UserReturnSchema,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, Pool


class NorthAdmin:
    """NorthAdmin base class.

    Arguments:
    ---------
        sqlalchemy_uri (str): SQLAlchemy connection string (e.q. postgresql://postgres:@127.0.0.1:5432/test_app)
        jwt_secret_key (str): JWT secret
        auth_provider (AuthProvider): Admin auth provider class (see AuthProvider docs)
        logo_url (str): Web link to admin panel logo
        sqlalchemy_pool_size (int): SQLAlchemy pool size (default no pull uses)
        sqlalchemy_pool_class (sqlalchemy.Pool): SQLAlchemy pool class (default NullPool)

    Methods:
    -------
        add_admin_routes (admin_router: AdminRouter): Add admin router (see AdminRouter docs)

    To integrate NorthAdmin app to FastAPI app user setup_admin functions.

    Return:
    ------
        NorthAdmin:NorthAdmin
    """

    router: APIRouter
    api_router: APIRouter
    frontend_router: APIRouter

    models_info: dict[str, ModelInfoDTO]
    logo_url: str | None

    _sqlalchemy_engine: AsyncEngine
    _sqlalchemy_session_maker: async_sessionmaker[AsyncSession]
    _jwt_secret_key: str
    _auth_provider: AuthProvider

    def __init__(
        self,
        sqlalchemy_uri: str,
        jwt_secret_key: str,
        auth_provider: Type[AuthProvider],
        logo_url: str | None = None,
        sqlalchemy_pool_size: int | None = None,
        sqlalchemy_pool_class: Pool = NullPool,
    ) -> None:
        self.router = APIRouter()
        self.api_router = APIRouter()
        self.frontend_router = APIRouter()

        self._jwt_secret_key = jwt_secret_key
        self.logo_url = logo_url
        self.models_info = {}

        sqlalchemy_engine_args = {
            "poolclass": sqlalchemy_pool_class,
        }
        if sqlalchemy_pool_class != NullPool and sqlalchemy_pool_size:
            sqlalchemy_engine_args["pool_size"] = sqlalchemy_pool_size

        self._sqlalchemy_engine = create_async_engine(
            sqlalchemy_uri,
            **sqlalchemy_engine_args,
        )

        self._sqlalchemy_session_maker = async_sessionmaker(
            bind=self._sqlalchemy_engine,
            expire_on_commit=False,
        )

        self._auth_provider = auth_provider(
            jwt_secret_key=jwt_secret_key,
            sqlalchemy_session_maker=self._sqlalchemy_session_maker,
        )

    async def _admin_info_route(self) -> dict[str, ModelInfoDTO]:
        return self.models_info

    def _setup_admin_info_route(self) -> None:
        self.api_router.get(
            path="/",
            response_model=dict[str, ModelInfoDTO],
            description="Info about admin API structure",
            tags=["Admin: Info"],
        )(self._admin_info_route)

    def _setup_admin_auth_route(self) -> None:
        self.api_router.post(
            path="/auth/login",
            response_model=JWTTokens,
            tags=["Admin: Auth"],
            description="Admin login method",
        )(self._auth_provider.login_endpoint)

        self.api_router.post(
            path="/token",
            response_model=JWTTokens,
            tags=["Admin: Auth"],
            description="Admin login method (service)",
        )(self._auth_provider.token_endpoint)

        self.api_router.get(
            path="/auth/users/current",
            response_model=UserReturnSchema,
            tags=["Admin: Auth"],
            description="Admin login method (service)",
        )(self._auth_provider.get_auth_user_endpoint)

    def add_admin_routes(
        self,
        admin_router: AdminRouter,
    ) -> None:
        """Add AdminRouter object to NA app.

        To find out more check out AdminRouter documentation.
        """

        logger.info("Initializing the NorthAdmin app.")

        admin_router.inject(
            sqlalchemy_session_maker=self._sqlalchemy_session_maker,
            auth_provider=self._auth_provider,
        )
        admin_router.setup_router()

        self.models_info[admin_router.model_id] = admin_router.model_info
        self._setup_admin_info_route()

        self.api_router.include_router(admin_router.router)

    def setup_router(self) -> None:
        """Setup main admin router."""

        self._setup_admin_auth_route()
        self.router.include_router(router=self.frontend_router)
        self.router.include_router(
            router=self.api_router,
            prefix="/api",
        )


def setup_admin(
    app: FastAPI,
    admin_app: NorthAdmin,
    admin_prefix: str = "/admin",
) -> FastAPI:
    """Include routes from NorthAdmin app to FastAPI app.

    Arguments:
    ---------
        app (FastAPI): target FastAPI application
        admin_app (NorthAdmin): NorthAdmin application
        admin_prefix (str): Prefix for admin API (default: /admin)

    Returns:
    -------
        FastAPI: FastAPI

    """
    admin_app.setup_router()

    app.include_router(
        prefix=admin_prefix,
        router=admin_app.router,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("NorthAdmin app was initialized!")

    return app
