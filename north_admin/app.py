from fastapi import FastAPI, APIRouter

from sqlalchemy.pool import Pool, NullPool
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
    AsyncSession,
)
from sqlalchemy.orm.attributes import InstrumentedAttribute

from north_admin.admin_router import AdminRouter
from north_admin.dto import ModelInfoDTO
from north_admin.types import ModelType, AdminMethods, FilterType


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
        model: ModelType,
        model_title: str | None = None,
        enabled_methods: list[AdminMethods] | None = None,
        pkey_column: InstrumentedAttribute | None = None,
        list_columns: list[InstrumentedAttribute] | None = None,
        get_columns: list[InstrumentedAttribute] | None = None,
        create_columns: list[InstrumentedAttribute] | None = None,
        update_columns: list[InstrumentedAttribute] | None = None,
        soft_delete_column: InstrumentedAttribute | None = None,
        sortable_columns: list[InstrumentedAttribute] | None = None,
        filters: dict[
          str,
          tuple[
              InstrumentedAttribute,
              FilterType,
          ],
        ] | None = None,
    ) -> None:
        admin_router = AdminRouter(
            model=model,
            sqlalchemy_session_maker=self.sqlalchemy_session_maker,
            model_title=model_title,
            enabled_methods=enabled_methods,
            list_columns=list_columns,
            get_columns=get_columns,
            create_columns=create_columns,
            update_columns=update_columns,
            soft_delete_column=soft_delete_column,
            sortable_columns=sortable_columns,
            filters=filters,
        )

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
