from fastapi import APIRouter, Depends
from pydantic import BaseModel, create_model
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from north_admin.crud import crud
from north_admin.dto import ModelInfoDTO, ColumnDTO
from north_admin.helpers import set_origin_to_pydantic_schema
from north_admin.types import ModelType, AdminMethods, FilterType, FieldAPIType, sqlalchemy_column_to_pydantic, \
    ColumnType


class AdminRouter:
    model: ModelType
    model_title: str

    router: APIRouter
    model_info: ModelInfoDTO
    model_columns: list[ColumnType]
    pkey_column: ColumnType
    key_columns: list[ColumnType]
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession]

    create_schema: BaseModel | None
    update_schema: BaseModel | None
    get_schema: BaseModel | None
    list_schema: BaseModel | None

    enabled_methods: list[AdminMethods]
    excluded_columns: list[ColumnType] | None = None
    list_columns: list[ColumnType]
    get_columns: list[ColumnType]
    create_columns: list[ColumnType]
    update_columns: list[ColumnType]
    soft_delete_column: ColumnType | None
    sortable_columns: list[ColumnType]
    filters: dict[
         str,
         tuple[
             ColumnType,
             FilterType,
         ],
    ] | None

    def __init__(
        self,
        model: ModelType,
        sqlalchemy_session_maker: async_sessionmaker[AsyncSession],
        model_title: str | None = None,
        enabled_methods: list[AdminMethods] | None = None,
        pkey_column: ColumnType | None = None,
        list_columns: list[ColumnType] | None = None,
        get_columns: list[ColumnType] | None = None,
        create_columns: list[ColumnType] | None = None,
        update_columns: list[ColumnType] | None = None,
        soft_delete_column: ColumnType | None = None,
        sortable_columns: list[ColumnType] | None = None,
        excluded_columns: list[ColumnType] | None = None,
        filters: dict[
            str,
            tuple[
                ColumnType,
                FilterType,
            ],
        ] | None = None,
    ):
        self.model = model
        self.model_id = str(self.model.__table__)
        self.model_title = model_title if model_title else self.model_id.capitalize()

        self.sqlalchemy_session_maker = sqlalchemy_session_maker
        self.router = APIRouter(
            prefix=f'/{self.model_id}',
            tags=[self.model_title]
        )

        self.get_schema = None
        self.list_schema = None
        self.create_schema = None
        self.update_schema = None

        self.enabled_methods = enabled_methods if enabled_methods else list(AdminMethods)
        self.soft_delete_column = soft_delete_column
        self.filters = filters
        self.excluded_columns = excluded_columns if excluded_columns else []

        if pkey_column:
            self.pkey_column = pkey_column
        else:
            try:
                self.pkey_column = getattr(self.model, 'id')
            except AttributeError:
                raise Exception(
                    f'Can`t determinate pkey field for {self.model_id} model.'
                    'Try to set it manually.'
                )

        self.model_columns = inspect(model).columns.values()

        self.key_columns = [
            field
            for field in self.model_columns
            if field.primary_key
        ]

        non_key_columns = [
            field
            for field in self.model_columns
            if field not in self.key_columns
        ]

        self.list_columns = list_columns if list_columns else self.model_columns
        self.get_columns = get_columns if get_columns else self.model_columns
        self.create_columns = create_columns if create_columns else non_key_columns
        self.update_columns = update_columns if update_columns else non_key_columns
        self.sortable_columns = sortable_columns if sortable_columns else self.key_columns

    def convert_item_id_to_model_type(
        self,
        item_id: int | str,
    ):
        python_type, _ = sqlalchemy_column_to_pydantic(column=self.pkey_column)
        return python_type(item_id)

    async def get_endpoint(
        self,
        item_id: int | str,
    ) -> BaseModel:
        async with self.sqlalchemy_session_maker() as session:
            return await crud.get_item(
                model=self.model,
                pkey_column=self.pkey_column,
                session=session,
                item_id=self.convert_item_id_to_model_type(item_id),
            )

    async def list_endpoint(
        self,
    ) -> BaseModel:
        async with self.sqlalchemy_session_maker() as session:
            raise NotImplementedError

    async def create_endpoint(
        self,
        origin: any,
    ) -> BaseModel:
        async with self.sqlalchemy_session_maker() as session:
            return await crud.create_item(
                session=session,
                model=self.model,
                origin=origin,
            )

    async def update_endpoint(
        self,
        origin: any,
        item_id: int | str,
    ) -> BaseModel:
        async with self.sqlalchemy_session_maker() as session:
            return await crud.update_item(
                session=session,
                model=self.model,
                pkey_column=self.pkey_column,
                item_id=self.convert_item_id_to_model_type(item_id),
                origin=origin,
            )

    async def delete_endpoint(
        self,
        item_id: int | str,
    ) -> dict:
        async with self.sqlalchemy_session_maker() as session:
            async with self.sqlalchemy_session_maker() as session:
                return await crud.update_item(
                    session=session,
                    model=self.model,
                    pkey_column=self.pkey_column,
                    item_id=self.convert_item_id_to_model_type(item_id),
                )

    async def soft_delete_endpoint(
        self,
        item_id: int | str,
    ) -> BaseModel:
        async with self.sqlalchemy_session_maker() as session:
            return await crud.update_item(
                session=session,
                model=self.model,
                pkey_column=self.pkey_column,
                item_id=self.convert_item_id_to_model_type(item_id),
                **{
                    self.soft_delete_column.key: False,
                },
            )

    async def restore_endpoint(
        self,
        item_id: int | str,
    ) -> BaseModel:
        async with self.sqlalchemy_session_maker() as session:
            return await crud.update_item(
                session=session,
                model=self.model,
                pkey_column=self.pkey_column,
                item_id=self.convert_item_id_to_model_type(item_id),
                **{
                    self.soft_delete_column.key: True,
                },
            )

    def create_models(
        self,
        **kwargs,
    ) -> BaseModel:
        return create_model(
            self.model_title,
            **kwargs,
        )

    def setup_router(self) -> None:
        self.model_info = ModelInfoDTO(
            title=self.model_title,
            columns={},
        )

        create_schema_items: dict[str, tuple[type, any]] = {}
        update_schema_items: dict[str, tuple[type, any]] = {}
        get_schema_items: dict[str, tuple[type, any]] = {}
        list_schema_items: dict[str, tuple[type, any]] = {}

        for field in self.model_columns:
            if field in self.excluded_columns:
                continue

            pydantic_params = sqlalchemy_column_to_pydantic(field)

            self.model_info.columns[field.key] = ColumnDTO(
                column_type=FieldAPIType.STRING,
                nullable=field.nullable,
                is_get_available=(field in self.get_columns),
                is_list_available=(field in self.list_columns),
                is_create_available=(field in self.create_columns),
                is_update_available=(field in self.update_columns),
                is_sortable=(field in self.sortable_columns),
            )

            if AdminMethods.GET_ONE in self.enabled_methods and field in self.get_columns:
                get_schema_items[field.key] = pydantic_params

            if AdminMethods.GET_LIST in self.enabled_methods and field in self.list_columns:
                list_schema_items[field.key] = pydantic_params

            if AdminMethods.CREATE in self.enabled_methods and field in self.create_columns:
                create_schema_items[field.key] = pydantic_params

            if AdminMethods.UPDATE in self.enabled_methods and field in self.update_columns:
                update_schema_items[field.key] = pydantic_params

        if AdminMethods.GET_LIST:
            self.list_schema = self.create_models(**list_schema_items)

            self.router.get(
                path='/',
                response_model=self.get_schema,
            )(self.list_endpoint)

        if AdminMethods.GET_ONE:
            self.get_schema = self.create_models(**get_schema_items)

            self.router.get(
                path='/{item_id}',
                response_model=self.get_schema,
            )(self.get_endpoint)

        if AdminMethods.CREATE:
            self.create_schema = self.create_models(**create_schema_items)

            decorated_endpoint = set_origin_to_pydantic_schema(
                schema=self.create_schema,
                function=self.create_endpoint,
            )

            self.router.post(
                path='/',
                response_model=self.get_schema,
            )(decorated_endpoint)

        if AdminMethods.UPDATE:
            self.update_schema = self.create_models(**update_schema_items)

            decorated_endpoint = set_origin_to_pydantic_schema(
                schema=self.update_schema,
                function=self.update_endpoint,
            )

            self.router.patch(
                path='/{item_id}',
                response_model=self.get_schema,
            )(decorated_endpoint)

        if AdminMethods.DELETE:
            self.router.delete(
                path='/{item_id}',
                response_model=dict,
            )(self.delete_endpoint)

        if AdminMethods.SOFT_DELETE:
            if not self.soft_delete_column:
                raise Exception(
                    f'To make soft delete for {self.model_title} model awailable set soft_delete_column params'
                )

            self.router.delete(
                path='/{item_id}/soft',
                response_model=self.get_schema,
            )(self.soft_delete_endpoint)

            self.router.get(
                path='/{item_id}/restore',
                response_model=self.get_schema,
            )(self.restore_endpoint)