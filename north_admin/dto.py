from pydantic import BaseModel

from north_admin.types import FieldAPIType


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
    columns: dict[str, ColumnDTO]
