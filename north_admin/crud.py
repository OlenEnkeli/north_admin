from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from north_admin.exceptions import NothingToUpdate
from north_admin.types import ModelType, ColumnType


class CRUD:
    async def get_item(
        self,
        session: AsyncSession,
        model: ModelType,
        pkey_column: ColumnType,
        item_id: int | str,
    ) -> ModelType:
        query = select(model).filter(pkey_column == item_id)
        item = await session.scalar(query)

        if not item:
            raise HTTPException(
                status_code=404,
                detail=f'Can`t find {model.__table__} with id {item_id}.',
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
        except (IntegrityError, DatabaseError) as e:
            raise HTTPException(
                status_code=500,
                detail=f'Can`t save item - {e}',
            )

        return item

    async def update_item(
        self,
        session: AsyncSession,
        model: ModelType,
        item_id: int | str,
        pkey_column: ColumnType,
        origin: BaseModel | None = None,
        **kwargs,
    ) -> ModelType:
        item = await self.get_item(
            session=session,
            model=model,
            pkey_column=pkey_column,
            item_id=item_id,
        )

        if not origin and not kwargs:
            raise NothingToUpdate(model_id=str(model.__table__), item_id=item_id)

        if origin:
            for key, value in origin.model_dump().items():
                setattr(item, key, value)

        for key, value in kwargs.items():
            setattr(item, key, value)

        try:
            await session.merge(item)
            await session.commit()
            await session.refresh(item)
        except (IntegrityError, DatabaseError) as e:
            raise HTTPException(
                status_code=500,
                detail=f'Can`t update item - {e}',
            )

        return item

    async def delete_item(
        self,
        session: AsyncSession,
        model: ModelType,
        item_id: int | str,
        pkey_column: ColumnType,
    ) -> dict:
        item = await self.get_item(
            session=session,
            model=model,
            pkey_column=pkey_column,
            item_id=item_id,
        )

        try:
            await session.delete(item)
            await session.commit()
        except (IntegrityError, DatabaseError) as e:
            raise HTTPException(
                status_code=500,
                detail=f'Can`t update item - {e}',
            )

        return {'success': 'ok'}


crud = CRUD()
