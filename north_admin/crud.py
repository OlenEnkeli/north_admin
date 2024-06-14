from typing import Any, Callable

from fastapi import HTTPException
from north_admin.exceptions import (
    DatabaseInternalError,
    ItemNotFoundExceptionError,
    NothingToUpdateError,
)
from north_admin.filters import FilterGroup
from north_admin.types import (
    ColumnType,
    ModelType,
    QueryType,
)
from pydantic import BaseModel
from sqlalchemy import (
    delete,
    func,
    select,
    update,
)
from sqlalchemy.exc import DatabaseError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class CRUD:
    async def get_item(
        self,
        session: AsyncSession,
        model: ModelType,
        pkey_column: ColumnType,
        item_id: int | str,
        process_query_method: Callable[[QueryType], QueryType] | None = None,
    ) -> ModelType:
        query = select(model).filter(pkey_column == item_id)
        if process_query_method:
            query = process_query_method(query)

        item = await session.scalar(query)

        if not item:
            raise ItemNotFoundExceptionError(
                model=model,
                item_id=item_id,
            )

        return item

    async def create_item(
        self,
        session: AsyncSession,
        model: ModelType,
        origin: BaseModel,
    ) -> ModelType:
        item = model(**origin.model_dump())

        try:
            session.add(item)
            await session.commit()
            await session.refresh(item)
        except (IntegrityError, DatabaseError) as error:
            raise DatabaseInternalError(
                model=model,
                exception=error,
            ) from error

        return item

    async def update_item(
        self,
        session: AsyncSession,
        model: ModelType,
        item_id: int | str,
        pkey_column: ColumnType,
        origin: BaseModel | None = None,
        process_query_method: Callable[[QueryType], QueryType] | None = None,
        **kwargs: dict[str, Any],
    ) -> ModelType:
        item = await self.get_item(
            session=session,
            model=model,
            pkey_column=pkey_column,
            item_id=item_id,
            process_query_method=process_query_method,
        )

        if not origin and not kwargs:
            raise NothingToUpdateError(model_id=str(model.__table__), item_id=item_id)

        if origin:
            for key, value in origin.model_dump().items():
                setattr(item, key, value)

        for key, value in kwargs.items():
            setattr(item, key, value)

        try:
            await session.merge(item)
            await session.commit()
            await session.refresh(item)
        except (IntegrityError, DatabaseError) as error:
            raise HTTPException(
                status_code=500,
                detail=f"Can`t update item - {error}",
            ) from error

        return item

    async def delete_item(
        self,
        session: AsyncSession,
        model: ModelType,
        item_id: int | str,
        pkey_column: ColumnType,
        process_query_method: Callable[[QueryType], QueryType] | None = None,
    ) -> dict:
        item = await self.get_item(
            session=session,
            model=model,
            pkey_column=pkey_column,
            item_id=item_id,
            process_query_method=process_query_method,
        )

        try:
            await session.delete(item)
            await session.commit()
        except (IntegrityError, DatabaseError) as error:
            raise DatabaseInternalError(
                model=model,
                exception=error,
            ) from error

        return {"success": "ok"}

    async def delete_multiply(
        self,
        session: AsyncSession,
        model: ModelType,
        pkey_column: ColumnType,
        item_ids: list[int | str],
        process_query_method: Callable[[QueryType], QueryType] | None = None,
    ) -> dict[str, str]:
        query = (
            delete(model)
            .filter(pkey_column.in_(item_ids))
        )

        if process_query_method:
            query = process_query_method(query)

        try:
            await session.execute(query)
            await session.commit()
        except (IntegrityError, DatabaseError) as error:
            raise DatabaseInternalError(
                model=model,
                exception=error,
            ) from error

        return {"success": "ok"}

    async def soft_delete_multiply(
        self,
        session: AsyncSession,
        model: ModelType,
        pkey_column: ColumnType,
        soft_delete_column: ColumnType,
        item_ids: list[int | str],
        process_query_method: Callable[[QueryType], QueryType] | None = None,
    ) -> dict[str, str]:
        query = (
            update(model)
            .where(pkey_column.in_(item_ids))
            .values(
                **{
                    soft_delete_column.key: False,
                },
            )
        )

        if process_query_method:
            query = process_query_method(query)

        try:
            await session.execute(query)
            await session.commit()
        except (IntegrityError, DatabaseError) as error:
            raise DatabaseInternalError(
                model=model,
                exception=error,
            ) from error

        return {"success": "ok"}

    async def list_items(
        self,
        session: AsyncSession,
        model: ModelType,
        pkey_column: ColumnType,
        soft_delete_column: ColumnType,
        page: int,
        pagination_size: int,
        *,
        sort_by: ColumnType | None,
        sort_asc: bool,
        soft_deleted_included: bool,
        filters: list[FilterGroup] | None,
        filters_values: dict[str, any] | None,
        process_query_method: Callable[[QueryType], QueryType] | None = None,
    ) -> tuple[int, list[ModelType]]:
        offset = pagination_size * (page - 1)

        query = (
            select(model)
            .offset(offset)
            .limit(pagination_size)
            .order_by(sort_by.asc() if sort_asc else sort_by.desc())
        )

        if process_query_method:
            query = process_query_method(query)

        if not soft_deleted_included:
            query = query.filter(soft_delete_column.is_(True))

        for current_filter in filters:
            params = current_filter.query.compile().params
            disable_filter: bool = False

            for key in params:
                if key not in filters_values:
                    continue

                if filters_values[key] is None:
                    disable_filter = True

            if disable_filter:
                continue
            query = query.filter(current_filter.query)

        items = await session.scalars(query, params=filters_values)

        query = select(func.count(pkey_column))
        total_amount = await session.scalar(query)

        return total_amount, list(items)


crud = CRUD()
