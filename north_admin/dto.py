from pydantic import BaseModel, ConfigDict
from sqlalchemy import BinaryExpression, BooleanClauseList
from sqlalchemy.orm import Query

from north_admin.types import FieldAPIType


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DTOBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class FilterDTO(DTOBase):
    title: str
    field_type: FieldAPIType


class FilterGroupDTO(DTOBase):
    query: Query | BinaryExpression | BooleanClauseList
    filters: list[FilterDTO]


class ColumnDTO(DTOBase):
    column_type: FieldAPIType
    nullable: bool

    is_get_available: bool
    is_list_available: bool
    is_create_available: bool
    is_update_available: bool
    is_sortable: bool


class ModelInfoDTO(DTOBase):
    title: str
    emoji: str
    pkey_column:  str
    soft_delete_column: str | None = None
    filters: list[FilterGroupDTO]
    columns: dict[str, ColumnDTO]
