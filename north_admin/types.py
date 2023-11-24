from datetime import datetime as dt
from enum import Enum
from typing import Self, Type

from sqlalchemy import Column, Select
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, Query


ModelType = Type[DeclarativeBase]
ColumnType = Column | InstrumentedAttribute | None
QueryType = Select | Query


class AdminMethods(str, Enum):
    GET_LIST = 'get_list'
    GET_ONE = 'get_one'
    CREATE = 'create'
    UPDATE = 'update'
    SOFT_DELETE = 'soft_delete'
    DELETE = 'delete'


class FieldType(str, Enum):
    INTEGER = 'integer'
    BOOLEAN = 'boolean'
    FLOAT = 'float'
    STRING = 'string'
    ENUM = 'enum'
    DATETIME = 'datetime'
    ARRAY = 'array'

    def to_python_type(self) -> Type:
        if self == FieldType.INTEGER:
            return int
        elif self == FieldType.BOOLEAN:
            return bool
        elif self == FieldType.FLOAT:
            return float
        elif self == FieldType.STRING:
            return str
        elif self == FieldType.ENUM:
            return Enum
        elif self == FieldType.DATETIME:
            return dt
        elif self == FieldType.ARRAY:
            return list

    @classmethod
    def from_python_type(cls, python_type: Type) -> Self:
        if python_type == int:
            return cls.INTEGER
        if python_type == bool:
            return cls.BOOLEAN
        elif python_type == float:
            return cls.FLOAT
        elif python_type == Enum:
            return cls.ENUM
        elif python_type == list or python_type == tuple:
            return cls.ARRAY
        elif python_type == dt:
            return cls.DATETIME
        else:
            return cls.STRING


def sqlalchemy_column_to_pydantic(column: ColumnType) -> tuple[type, any]:
    """
    :param column: InstrumentedAttribute (SQLAlchemy column)
    :return: (python_type: type, default: any)
    """

    python_type: type | None = None
    default: any = column.default

    if hasattr(column.type, 'impl'):
        if hasattr(column.type.impl, 'python_type'):
            python_type = column.type.impl.python_type

    elif hasattr(column.type, 'python_type'):
        python_type = column.type.python_type

    if column.default is None and not column.nullable:
        default = ...

    return python_type, default
