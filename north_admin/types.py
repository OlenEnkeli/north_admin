from datetime import datetime as dt
from enum import Enum
from typing import Self, Type

from sqlalchemy import Column, Select
from sqlalchemy.orm import (
    DeclarativeBase,
    InstrumentedAttribute,
    Query,
)

ModelType = Type[DeclarativeBase]
ColumnType = Column | InstrumentedAttribute | None
QueryType = Select | Query


class AdminMethods(str, Enum):
    GET_LIST = "get_list"
    GET_ONE = "get_one"
    CREATE = "create"
    UPDATE = "update"
    SOFT_DELETE = "soft_delete"
    DELETE = "delete"


class FieldType(str, Enum):
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    STRING = "string"
    ENUM = "enum"
    DATETIME = "datetime"
    ARRAY = "array"

    def to_python_type(self) -> Type:
        return {
            FieldType.INTEGER: int,
            FieldType.BOOLEAN: bool,
            FieldType.FLOAT: float,
            FieldType.STRING: str,
            FieldType.ENUM: Enum,
            FieldType.DATETIME: dt,
            FieldType.ARRAY: list,
        }.get(self, str)

    @classmethod
    def from_python_type(cls, python_type: Type) -> Self:
        return {
            int: cls.INTEGER,
            bool: cls.BOOLEAN,
            float: cls.FLOAT,
            str: cls.STRING,
            Enum: cls.ENUM,
            list: cls.ARRAY,
            tuple: cls.ARRAY,
            dt: cls.DATETIME,
        }.get(python_type, cls.STRING)


def sqlalchemy_column_to_pydantic(column: ColumnType) -> tuple[type, any]:
    """Convert SQLAlchemy column type to Pydantic type.

    Params:
        column (ColumnType)

    :return: (python_type: type, default: any)
    """
    python_type: type | None = None
    default: any = column.default

    if hasattr(column.type, "impl"):
        if hasattr(column.type.impl, "python_type"):
            python_type = column.type.impl.python_type

    elif hasattr(column.type, "python_type"):
        python_type = column.type.python_type

    if column.default is None and not column.nullable:
        default = ...

    return python_type, default
