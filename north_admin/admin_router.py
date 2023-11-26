from functools import reduce
from typing import Callable, Type

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from north_admin.auth_provider import AuthProvider
from north_admin.crud import crud
from north_admin.dto import ColumnDTO, ModelInfoDTO, ORMBase
from north_admin.exceptions import NoDefinedPKException, NoSoftDeleteField, PKeyMustBeInList
from north_admin.filters import FilterGroup
from north_admin.helpers import filters_dict, generate_random_emoji, set_origin_to_pydantic_schema
from north_admin.types import (
    AdminMethods,
    ColumnType,
    FieldType,
    ModelType,
    QueryType,
    sqlalchemy_column_to_pydantic,
)
from pydantic import BaseModel, ValidationError, create_model
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AdminRouter:
    auth_provider: AuthProvider
    model: ModelType
    model_title: str
    emoji: str

    router: APIRouter
    model_info: ModelInfoDTO
    model_columns: list[ColumnType]
    pkey_column: ColumnType
    key_columns: list[ColumnType]
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession]
    pagination_size: int

    create_schema: BaseModel | None
    update_schema: BaseModel | None
    get_schema: BaseModel | None
    list_schema_one: BaseModel | None
    list_schema: BaseModel | None
    filters_schema: BaseModel | None

    enabled_methods: list[AdminMethods]
    process_query_method: Callable[[QueryType], QueryType]
    excluded_columns: list[ColumnType] | None = None
    list_columns: list[ColumnType]
    get_columns: list[ColumnType]
    create_columns: list[ColumnType]
    update_columns: list[ColumnType]
    soft_delete_column: ColumnType | None
    sortable_columns: list[ColumnType]
    filters: list[FilterGroup] | None = None

    def __init__(
        self,
        model: ModelType,
        emoji: str | None = None,
        model_title: str | None = None,
        process_query_method: Callable[[QueryType], QueryType] | None = None,
        enabled_methods: list[AdminMethods] | None = None,
        pkey_column: ColumnType | None = None,
        list_columns: list[ColumnType] | None = None,
        get_columns: list[ColumnType] | None = None,
        create_columns: list[ColumnType] | None = None,
        update_columns: list[ColumnType] | None = None,
        soft_delete_column: ColumnType | None = None,
        sortable_columns: list[ColumnType] | None = None,
        excluded_columns: list[ColumnType] | None = None,
        pagination_size: int = 100,
        filters: list[FilterGroup] | None = None,
    ):
        self.model = model
        self.model_id = str(self.model.__table__)
        self.model_title = model_title if model_title else self.model_id.capitalize()
        self.emoji = emoji if emoji else generate_random_emoji()
        self.pagination_size = pagination_size

        logger.debug(f'Adding admin pages for {self.model_id} model...')

        self.get_schema = None
        self.list_schema_one = None
        self.create_schema = None
        self.update_schema = None

        self.process_query_method = process_query_method
        self.enabled_methods = enabled_methods if enabled_methods else list(AdminMethods)
        self.soft_delete_column = soft_delete_column if soft_delete_column else None
        self.filters = filters if filters else []
        self.excluded_columns = excluded_columns if excluded_columns else []

        if pkey_column:
            self.pkey_column = pkey_column
        else:
            try:
                self.pkey_column = self.model.id
            except AttributeError:
                raise NoDefinedPKException(model_id=self.model_id) from None

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

        if self.pkey_column not in self.list_columns:
            raise PKeyMustBeInList(self.model_id)

    def inject(
        self,
        sqlalchemy_session_maker: async_sessionmaker[AsyncSession],
        auth_provider: AuthProvider,
    ):
        self.sqlalchemy_session_maker = sqlalchemy_session_maker
        self.auth_provider = auth_provider

        self.router = APIRouter(
            prefix=f'/{self.model_id}',
            tags=[f'Admin: {self.model_title}'],
            dependencies=[Depends(self.auth_provider.get_auth_user)]
        )

        logger.info(f'Admin pages for {self.model_id} model is up and ready.')

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
                process_query_method=self.process_query_method,
            )

    async def list_endpoint(
        self,
        page: int = 1,
        sort_by: str | None = None,
        soft_deleted_included: bool = True,
        filters: str = Depends(filters_dict),
    ) -> BaseModel:
        parsed_filters: dict[str, any]

        try:
            parsed_filters = self.filters_schema.model_validate(filters).model_dump()
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=f'Can`t parse filters: {e}',
            ) from e
        async with self.sqlalchemy_session_maker() as session:
            total_amount, items = await crud.list_items(
                session=session,
                model=self.model,
                pkey_column=self.pkey_column,
                soft_deleted_included=soft_deleted_included,
                soft_delete_column=self.soft_delete_column,
                page=page,
                pagination_size=self.pagination_size,
                sort_by=sort_by,
                filters=self.filters,
                filters_values=parsed_filters,
                process_query_method=self.process_query_method,
            )

            return self.list_schema( # noqa
                page=page,
                pagination_size=self.pagination_size,
                total_amount=total_amount,
                current_page_amount=len(items),
                items=[self.list_schema_one.model_validate(item) for item in items],
            )

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
                process_query_method=self.process_query_method,
            )

    async def delete_endpoint(
        self,
        item_id: int | str,
    ) -> dict:
        async with self.sqlalchemy_session_maker() as session:
            return await crud.update_item(
                session=session,
                model=self.model,
                pkey_column=self.pkey_column,
                item_id=self.convert_item_id_to_model_type(item_id),
                process_query_method=self.process_query_method,
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
                process_query_method=self.process_query_method,
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
                process_query_method=self.process_query_method,
            )

    def create_models(
        self,
        **kwargs,
    ) -> BaseModel:
        return create_model(
            self.model_title,
            __config__=ORMBase.model_config,
            **kwargs,
        )

    def setup_router(self) -> None:
        self.model_info = ModelInfoDTO(
            title=self.model_title,
            emoji=self.emoji,
            columns={},
            pkey_column=self.pkey_column.key,
            filters=reduce(
                lambda fg_left, fg_right: fg_left.filter_dto_list() + fg_right.filter_dto_list(),
                self.filters,
            ),
            soft_delete_column=self.soft_delete_column.key if self.soft_delete_column else None,
        )

        create_schema_items: dict[str, tuple[type, any]] = {}
        update_schema_items: dict[str, tuple[type, any]] = {}
        get_schema_items: dict[str, tuple[type, any]] = {}
        list_schema_items: dict[str, tuple[type, any]] = {}

        for column in self.model_columns:
            if column in self.excluded_columns:
                continue

            pydantic_params = sqlalchemy_column_to_pydantic(column)

            self.model_info.columns[column.key] = ColumnDTO(
                column_type=FieldType.from_python_type(pydantic_params[0]),
                nullable=column.nullable,
                is_get_available=(column in self.get_columns),
                is_list_available=(column in self.list_columns),
                is_create_available=(column in self.create_columns),
                is_update_available=(column in self.update_columns),
                is_sortable=(column in self.sortable_columns),
            )

            if AdminMethods.GET_ONE in self.enabled_methods and column in self.get_columns:
                get_schema_items[column.key] = pydantic_params

            if AdminMethods.GET_LIST in self.enabled_methods and column in self.list_columns:
                list_schema_items[column.key] = pydantic_params

            if AdminMethods.CREATE in self.enabled_methods and column in self.create_columns:
                create_schema_items[column.key] = pydantic_params

            if AdminMethods.UPDATE in self.enabled_methods and column in self.update_columns:
                update_schema_items[column.key] = pydantic_params

        if AdminMethods.GET_LIST in self.enabled_methods:
            self.list_schema_one = self.create_models(**list_schema_items)
            self.list_schema = self.create_models(
                **{
                    'page': (int, ...),
                    'pagination_size': (int, ...),
                    'current_page_amount': (int, ...),
                    'total_amount': (int, ...),
                    'items': (list[self.list_schema_one], ...),
                }
            )

            parsed_filters: dict[str, tuple[Type, any]] = {}

            for current_filter_group in self.filters:
                for current_filter in current_filter_group.filters:
                    parsed_filters[current_filter.bindparam] = (
                        current_filter.field_type.to_python_type(),
                        None,
                    )

            self.filters_schema = self.create_models(**parsed_filters)

            self.router.get(
                path='/',
                response_model=self.list_schema,
            )(self.list_endpoint)

        if AdminMethods.GET_ONE in self.enabled_methods:
            self.get_schema = self.create_models(**get_schema_items)

            self.router.get(
                path='/{item_id}',
                response_model=self.get_schema,
            )(self.get_endpoint)

        if AdminMethods.CREATE in self.enabled_methods:
            self.create_schema = self.create_models(**create_schema_items)

            decorated_endpoint = set_origin_to_pydantic_schema(
                schema=self.create_schema,
                function=self.create_endpoint,
            )

            self.router.post(
                path='/',
                response_model=self.get_schema,
            )(decorated_endpoint)

        if AdminMethods.UPDATE in self.enabled_methods:
            self.update_schema = self.create_models(**update_schema_items)

            decorated_endpoint = set_origin_to_pydantic_schema(
                schema=self.update_schema,
                function=self.update_endpoint,
            )

            self.router.patch(
                path='/{item_id}',
                response_model=self.get_schema,
            )(decorated_endpoint)

        if AdminMethods.DELETE in self.enabled_methods:
            self.router.delete(
                path='/{item_id}',
                response_model=dict,
            )(self.delete_endpoint)

        if AdminMethods.SOFT_DELETE in self.enabled_methods:
            if not self.soft_delete_column:
                raise NoSoftDeleteField(model_id=self.model_id)

            self.router.delete(
                path='/{item_id}/soft',
                response_model=self.get_schema,
            )(self.soft_delete_endpoint)

            self.router.get(
                path='/{item_id}/restore',
                response_model=self.get_schema,
            )(self.restore_endpoint)
