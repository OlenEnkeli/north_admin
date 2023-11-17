from fastapi import APIRouter, Depends
from pydantic import BaseModel, create_model
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from north_admin.dto import ModelInfoDTO, ColumnDTO
from north_admin.types import ModelType, AdminMethods, FilterType, FieldAPIType, sqlalchemy_column_to_pydantic


class AdminRouter:
    model: ModelType
    model_title: str

    router: APIRouter
    model_info: ModelInfoDTO
    model_columns: list[InstrumentedAttribute]
    key_columns: list[InstrumentedAttribute]
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession]

    create_schema: BaseModel | None
    update_schema: BaseModel | None
    get_schema: BaseModel | None
    list_schema: BaseModel | None

    enabled_methods: list[AdminMethods]
    list_columns: list[InstrumentedAttribute]
    get_columns: list[InstrumentedAttribute]
    create_columns: list[InstrumentedAttribute]
    update_columns: list[InstrumentedAttribute]
    soft_delete_column: InstrumentedAttribute | None
    sortable_columns: list[InstrumentedAttribute]
    filters: dict[
         str,
         tuple[
             InstrumentedAttribute,
             FilterType,
         ],
    ] | None

    def __init__(
        self,
        model: ModelType,
        sqlalchemy_session_maker: async_sessionmaker[AsyncSession],
        model_title: str | None = None,
        enabled_methods: list[AdminMethods] | None = None,
        list_columns: list[InstrumentedAttribute] | None = None,
        get_columns: list[InstrumentedAttribute] | None = None,
        create_columns: list[InstrumentedAttribute] | None = None,
        update_columns: list[InstrumentedAttribute] | None = None,
        soft_delete_field: InstrumentedAttribute | None = None,
        sortable_columns: list[InstrumentedAttribute] | None = None,
        filters: dict[
            str,
            tuple[
                InstrumentedAttribute,
                FilterType,
            ],
        ] | None = None,
    ):
        self.model = model
        self.model_id = str(self.model.__table__)

        self.sqlalchemy_session_maker = sqlalchemy_session_maker
        self.router = APIRouter(prefix=f'/{self.model_id}')

        self.get_schema = None
        self.list_schema = None
        self.create_schema = None
        self.update_schema = None

        self.enabled_methods = enabled_methods if enabled_methods else list(AdminMethods)
        self.soft_delete_column = soft_delete_field
        self.filters = filters

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

        self.model_title = model_title if model_title else self.model_id.capitalize()
        self.list_columns = list_columns if list_columns else self.model_columns
        self.get_columns = get_columns if get_columns else self.model_columns
        self.create_columns = create_columns if create_columns else non_key_columns
        self.update_columns = update_columns if update_columns else non_key_columns
        self.sortable_columns = sortable_columns if sortable_columns else self.key_columns

    async def get_endpoint(
        self,
        item_id: int | str,
    ):
        async with self.sqlalchemy_session_maker() as session:
            return None

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

        if AdminMethods.GET_ONE:
            self.get_schema = create_model(
                self.model_title,
                **get_schema_items,
            )

            self.router.get(
                path='/{item_id}',
                response_model=self.get_schema,
            )(self.get_endpoint)

        if AdminMethods.GET_LIST:
            self.list_schema = create_model(
                self.model_title,
                **list_schema_items,
            )

        if AdminMethods.CREATE:
            self.create_schema = create_model(
                self.model_title,
                **create_schema_items,
            )

        if AdminMethods.UPDATE:
            self.update_schema = create_model(
                self.model_title,
                **update_schema_items,
            )

