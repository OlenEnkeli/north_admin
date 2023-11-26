from typing import Type

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from north_admin.admin_router import AdminRouter
from north_admin.auth_provider import AuthProvider
from north_admin.dto import JWTTokens, ModelInfoDTO, UserReturnSchema
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, Pool


class NorthAdmin:
    router: APIRouter
    api_router: APIRouter
    frontend_router: APIRouter

    models_info: dict[str, ModelInfoDTO]
    logo_url: str | None

    sqlalchemy_engine: AsyncEngine
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession]
    jwt_secket_key: str
    auth_provider: AuthProvider

    def __init__(
        self,
        sqlalchemy_uri: str,
        jwt_secket_key: str,
        auth_provider: Type[AuthProvider],
        logo_url: str | None = None,
        sqlalchemy_pool_size: int | None = None,
        sqlalchemy_pool_class: Pool = NullPool,
    ):
        self.router = APIRouter()
        self.api_router = APIRouter()
        self.frontend_router = APIRouter()

        self.jwt_secket_key = jwt_secket_key
        self.logo_url = logo_url
        self.models_info = {}

        sqlalchemy_engine_args = {
            'poolclass': sqlalchemy_pool_class,
        }
        if sqlalchemy_pool_class != NullPool and sqlalchemy_pool_size:
            sqlalchemy_engine_args['pool_size'] = sqlalchemy_pool_size

        self.sqlalchemy_engine = create_async_engine(
            sqlalchemy_uri,
            **sqlalchemy_engine_args,
        )

        self.sqlalchemy_session_maker = async_sessionmaker(
            bind=self.sqlalchemy_engine,
            expire_on_commit=False,
        )

        self.auth_provider = auth_provider(
            jwt_secret_key=jwt_secket_key,
            sqlalchemy_session_maker=self.sqlalchemy_session_maker,
        )

    async def admin_info_route(self) -> dict[str, ModelInfoDTO]:
        return self.models_info

    def setup_admin_info_route(self) -> None:
        self.api_router.get(
            path='/',
            response_model=dict[str, ModelInfoDTO],
            description='Info about admin API structure',
            tags=['Admin: Info'],
        )(self.admin_info_route)

    def setup_admin_auth_route(self) -> None:
        self.api_router.post(
            path='/auth/login',
            response_model=JWTTokens,
            tags=['Admin: Auth'],
            description='Admin login method',
        )(self.auth_provider.login_endpoint)

        self.api_router.post(
            path='/token',
            response_model=JWTTokens,
            tags=['Admin: Auth'],
            description='Admin login method (service)',
        )(self.auth_provider.token_endpoint)

        self.api_router.get(
            path='/auth/users/current',
            response_model=UserReturnSchema,
            tags=['Admin: Auth'],
            description='Admin login method (service)',
        )(self.auth_provider.get_auth_user_endpoint)

    def add_admin_routes(
        self,
        admin_router: AdminRouter,
    ) -> None:
        logger.debug('Starting the NorthAdmin app...')

        admin_router.inject(
            sqlalchemy_session_maker=self.sqlalchemy_session_maker,
            auth_provider=self.auth_provider,
        )
        admin_router.setup_router()

        self.models_info[admin_router.model_id] = admin_router.model_info
        self.setup_admin_info_route()

        self.api_router.include_router(admin_router.router)

    def setup_router(self) -> None:
        self.setup_admin_auth_route()
        self.router.include_router(router=self.frontend_router)
        self.router.include_router(
            router=self.api_router,
            prefix='/api',
        )


def setup_admin(
    app: FastAPI,
    admin_app: NorthAdmin,
    admin_prefix: str = '/admin',
):
    admin_app.setup_router()

    app.include_router(
        prefix=admin_prefix,
        router=admin_app.router,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    logger.info('NorthAdmin app was started and adding to main app.')
