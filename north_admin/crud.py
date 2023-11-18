from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from fastapi import HTTPException

from north_admin.types import ModelType


class CRUD:
    async def get_item(
        self,
        model: ModelType,
        pkey_column: InstrumentedAttribute,
        session: AsyncSession,
        item_id: int | str,
    ) -> any:
        query = select(model).filter(pkey_column == item_id)
        item = await session.scalar(query)

        if not item:
            raise HTTPException(
                status_code=404,
                detail=f'Can`t find {model.__table__} with id {item_id}.',
            )

        return item



crud = CRUD()
