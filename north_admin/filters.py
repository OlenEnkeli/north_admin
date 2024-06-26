from north_admin.dto import FilterDTO
from north_admin.types import FieldType
from sqlalchemy import BinaryExpression, BooleanClauseList
from sqlalchemy.orm import Query


class Filter:
    title: str
    field_type: FieldType
    bindparam: str

    def __init__(
        self,
        title: str,
        field_type: FieldType,
        bindparam: str,
    ) -> None:
        self.bindparam = bindparam
        self.title = title
        self.field_type = field_type


class FilterGroup:
    query: Query | BinaryExpression | BooleanClauseList
    filters: list[Filter]

    def __init__(
        self,
        query: Query | BinaryExpression | BooleanClauseList,
        filters: list[Filter],
    ) -> None:
        self.query = query
        self.filters = filters

    def filter_dto_list(self) -> list[FilterDTO]:
        return [
            FilterDTO(
                title=current_filter.title,
                field_type=current_filter.field_type,
                name=current_filter.bindparam,
            )
            for current_filter in self.filters
        ]
