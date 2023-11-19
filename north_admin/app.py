from fastapi import APIRouter, FastAPI
from north_admin.admin_router import AdminRouter
from north_admin.dto import ModelInfoDTO
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

    def __init__(
        self,
        sqlalchemy_uri: str,
        logo_url: str | None = None,
        sqlalchemy_pool_size: int | None = None,
        sqlalchemy_pool_class: Pool = NullPool,
    ):
        self.router = APIRouter()
        self.api_router = APIRouter()
        self.frontend_router = APIRouter()

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

    async def admin_info_route(self) -> dict[str, ModelInfoDTO]:
        return self.models_info

    def setup_admin_info_route(self) -> None:
        self.api_router.get(
            path='/',
            response_model=dict[str, ModelInfoDTO],
            description='Info about admin API structure',
            tags=['Admin info'],
        )(self.admin_info_route)

    def add_admin_routes(
        self,
        admin_router: AdminRouter,
    ) -> None:
        admin_router.inject_sqlalchemy(sqlalchemy_session_maker=self.sqlalchemy_session_maker)
        admin_router.setup_router()

        self.models_info[admin_router.model_id] = admin_router.model_info
        self.setup_admin_info_route()

        self.api_router.include_router(admin_router.router)

    def setup_router(self) -> None:
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
