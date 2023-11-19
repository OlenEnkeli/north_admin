from pydantic import BaseModel, ConfigDict

from north_admin.types import FieldAPIType


class ORMTable(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ColumnDTO(BaseModel):
    column_type: FieldAPIType
    nullable: bool

    is_get_available: bool
    is_list_available: bool
    is_create_available: bool
    is_update_available: bool
    is_sortable: bool


class ModelInfoDTO(BaseModel):
    title: str
    emoji: str
    pkey_column:  str
    soft_delete_column: str | None = None
    columns: dict[str, ColumnDTO]
